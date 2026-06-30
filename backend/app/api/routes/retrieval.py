from fastapi import APIRouter

from app.api.dependencies.auth import CurrentUserDep, WorkspaceContextDep
from app.db.session import DBSessionDep
from app.schemas.retrieval import RetrievalSearchRequest, RetrievalSearchResponse
from app.services.retrieval import search_workspace_chunks

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalSearchResponse)
def search_retrieval(
    payload: RetrievalSearchRequest,
    workspace_context: WorkspaceContextDep,
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> RetrievalSearchResponse:
    return search_workspace_chunks(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        current_user=current_user,
        membership_role=workspace_context.membership.role,
        request=payload,
    )
