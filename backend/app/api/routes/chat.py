from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.dependencies.auth import CurrentUserDep, WorkspaceContextDep
from app.core.config import get_settings
from app.db.session import DBSessionDep
from app.schemas.chat import (
    ChatAskRequest,
    ChatAskResponse,
    ConversationDetail,
    ConversationSummary,
)
from app.services.chat import (
    ask_question,
    delete_conversation,
    get_conversation_detail,
    list_conversations,
)

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


@router.get("/conversations", response_model=list[ConversationSummary])
def get_conversations(
    workspace_context: WorkspaceContextDep,
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> list[ConversationSummary]:
    return list_conversations(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        user_id=current_user.id,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: UUID,
    workspace_context: WorkspaceContextDep,
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> ConversationDetail:
    return get_conversation_detail(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )


@router.post("/ask", response_model=ChatAskResponse)
def ask_chat_question(
    payload: ChatAskRequest,
    workspace_context: WorkspaceContextDep,
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> ChatAskResponse:
    return ask_question(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        user=current_user,
        membership_role=workspace_context.membership.role,
        question=payload.question,
        conversation_id=payload.conversation_id,
        top_k=settings.retrieval_top_k_default,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_chat_conversation(
    conversation_id: UUID,
    workspace_context: WorkspaceContextDep,
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> Response:
    delete_conversation(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
