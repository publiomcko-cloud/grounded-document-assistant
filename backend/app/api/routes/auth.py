from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUserDep, DBSessionDep
from app.models import User, Workspace, WorkspaceMembership
from app.schemas.auth import (
    AuthUserResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.workspace import WorkspaceMembershipSummary, WorkspaceSummary
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_user_with_workspace,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def build_memberships(db: Session, user: User) -> list[WorkspaceMembershipSummary]:
    memberships = list(
        db.scalars(
            select(WorkspaceMembership).where(WorkspaceMembership.user_id == user.id)
        )
    )
    workspaces = {
        workspace.id: workspace
        for workspace in db.scalars(
            select(Workspace).where(
                Workspace.id.in_(
                    [membership.workspace_id for membership in memberships]
                )
            )
        )
    }

    return [
        WorkspaceMembershipSummary(
            workspace_id=membership.workspace_id,
            role=membership.role,
            workspace=WorkspaceSummary.model_validate(
                workspaces[membership.workspace_id]
            ),
        )
        for membership in memberships
        if membership.workspace_id in workspaces
    ]


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    payload: RegisterRequest,
    db: DBSessionDep,
) -> UserResponse:
    try:
        user = create_user_with_workspace(
            db,
            name=payload.name,
            email=payload.email,
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: DBSessionDep,
) -> TokenResponse:
    user = authenticate_user(
        db,
        email=payload.email,
        password=payload.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=AuthUserResponse)
def me(
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> AuthUserResponse:
    return AuthUserResponse(
        **UserResponse.model_validate(current_user).model_dump(),
        memberships=build_memberships(db, current_user),
    )
