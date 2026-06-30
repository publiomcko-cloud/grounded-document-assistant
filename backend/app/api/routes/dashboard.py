from fastapi import APIRouter

from app.api.dependencies.auth import CurrentUserDep, WorkspaceContextDep
from app.db.session import DBSessionDep
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import get_workspace_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    workspace_context: WorkspaceContextDep,
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> DashboardSummaryResponse:
    return get_workspace_dashboard_summary(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        user_id=current_user.id,
        membership_role=workspace_context.membership.role,
    )
