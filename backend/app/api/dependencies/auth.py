import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User, Workspace, WorkspaceMembership
from app.models.enums import WorkspaceRole
from app.services.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
TokenDep = Annotated[str, Depends(oauth2_scheme)]
DBSessionDep = Annotated[Session, Depends(get_db)]


@dataclass
class WorkspaceAccessContext:
    membership: WorkspaceMembership
    workspace: Workspace


def get_current_user(
    token: TokenDep,
    db: DBSessionDep,
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_access_token(token)
    except ValueError as exc:
        raise credentials_error from exc

    user = db.get(User, user_id)
    if user is None:
        raise credentials_error

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_current_membership(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
) -> WorkspaceAccessContext:
    if x_workspace_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Workspace-Id header is required",
        )

    try:
        workspace_id = uuid.UUID(x_workspace_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Workspace-Id must be a valid UUID",
        ) from exc

    membership = db.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == current_user.id,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    workspace = db.get(Workspace, membership.workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return WorkspaceAccessContext(membership=membership, workspace=workspace)


WorkspaceContextDep = Annotated[WorkspaceAccessContext, Depends(get_current_membership)]


def require_workspace_role(
    *allowed_roles: WorkspaceRole,
) -> Callable[[WorkspaceAccessContext], WorkspaceAccessContext]:
    def dependency(
        context: WorkspaceContextDep,
    ) -> WorkspaceAccessContext:
        if context.membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required workspace role",
            )

        return context

    return dependency
