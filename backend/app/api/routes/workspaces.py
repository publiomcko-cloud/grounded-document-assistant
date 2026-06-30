from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies.auth import CurrentUserDep, DBSessionDep, WorkspaceContextDep
from app.models import Workspace, WorkspaceMembership
from app.schemas.workspace import (
    ActiveWorkspaceResponse,
    WorkspaceMembershipSummary,
    WorkspaceSummary,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceMembershipSummary])
def list_workspaces(
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> list[WorkspaceMembershipSummary]:
    memberships = list(
        db.scalars(
            select(WorkspaceMembership).where(
                WorkspaceMembership.user_id == current_user.id
            )
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


@router.get("/active", response_model=ActiveWorkspaceResponse)
def active_workspace(
    context: WorkspaceContextDep,
) -> ActiveWorkspaceResponse:
    return ActiveWorkspaceResponse(
        workspace_id=context.membership.workspace_id,
        role=context.membership.role,
        workspace=WorkspaceSummary.model_validate(context.workspace),
    )
