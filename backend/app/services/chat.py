import uuid
from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import Conversation, Document, Message, MessageCitation, User
from app.models.enums import MessageRole
from app.schemas.chat import (
    ChatAskResponse,
    CitationResponse,
    ConversationDetail,
    ConversationSummary,
    MessageResponse,
)
from app.schemas.retrieval import RetrievalSearchRequest
from app.services.answers import (
    SAFE_INSUFFICIENT_CONTEXT_ANSWER,
    AnswerProviderError,
    get_answer_provider,
)
from app.services.retrieval import search_workspace_chunks


@dataclass
class ConversationContext:
    conversation: Conversation
    messages: list[Message]
    citations_by_message: dict[uuid.UUID, list[MessageCitation]]
    documents_by_id: dict[uuid.UUID, Document]


def list_conversations(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[ConversationSummary]:
    conversations = list(
        db.scalars(
            select(Conversation)
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.user_id == user_id,
            )
            .order_by(Conversation.updated_at.desc())
        )
    )
    if not conversations:
        return []

    conversation_ids = [conversation.id for conversation in conversations]
    message_counts = {
        row[0]: row[1]
        for row in db.execute(
            select(Message.conversation_id, func.count(Message.id))
            .where(Message.conversation_id.in_(conversation_ids))
            .group_by(Message.conversation_id)
        ).all()
    }
    latest_messages: dict[uuid.UUID, str] = {}
    for message in db.execute(
        select(Message)
        .where(Message.conversation_id.in_(conversation_ids))
        .order_by(Message.created_at.desc())
    ).scalars():
        latest_messages.setdefault(message.conversation_id, message.content)

    return [
        ConversationSummary(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=message_counts.get(conversation.id, 0),
            last_message_preview=_preview_text(latest_messages.get(conversation.id)),
        )
        for conversation in conversations
    ]


def get_conversation_detail(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> ConversationDetail:
    context = _load_conversation_context(
        db,
        workspace_id=workspace_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    return _serialize_conversation_detail(context)


def ask_question(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user: User,
    membership_role,
    question: str,
    conversation_id: uuid.UUID | None,
    top_k: int,
) -> ChatAskResponse:
    normalized_question = question.strip()
    if not normalized_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is required",
        )

    conversation = _resolve_or_create_conversation(
        db,
        workspace_id=workspace_id,
        user_id=user.id,
        question=normalized_question,
        conversation_id=conversation_id,
    )

    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=normalized_question,
    )
    db.add(user_message)
    db.flush()

    retrieval_response = search_workspace_chunks(
        db,
        workspace_id=workspace_id,
        current_user=user,
        membership_role=membership_role,
        request=RetrievalSearchRequest(
            query=normalized_question,
            top_k=top_k,
            strategy="hybrid",
        ),
    )

    answer_provider = get_answer_provider()
    try:
        answer_result = answer_provider.generate_answer(
            question=normalized_question,
            retrieved_chunks=retrieval_response.results,
        )
    except AnswerProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not generate answer: {exc}",
        ) from exc

    validated_chunk_ids = _validate_citation_chunk_ids(
        cited_chunk_ids=answer_result.citation_chunk_ids,
        retrieved_chunks=retrieval_response.results,
    )
    insufficient_context = bool(
        answer_result.insufficient_context
        or (not validated_chunk_ids and bool(retrieval_response.results))
    )
    answer_text = (
        SAFE_INSUFFICIENT_CONTEXT_ANSWER
        if insufficient_context
        else answer_result.answer.strip()
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=answer_text,
        retrieval_metadata={
            "query": normalized_question,
            "strategy_requested": retrieval_response.strategy_requested,
            "strategy_used": retrieval_response.strategy_used,
            "retrieved_chunk_ids": [
                str(result.chunk_id) for result in retrieval_response.results
            ],
            "insufficient_context": insufficient_context,
        },
        model_name=answer_result.model_name,
        token_usage=answer_result.token_usage,
    )
    db.add(assistant_message)
    db.flush()

    _persist_citations(
        db,
        message_id=assistant_message.id,
        retrieved_chunks=retrieval_response.results,
        validated_chunk_ids=validated_chunk_ids,
        insufficient_context=insufficient_context,
    )

    conversation.updated_at = func.now()
    db.commit()

    context = _load_conversation_context(
        db,
        workspace_id=workspace_id,
        user_id=user.id,
        conversation_id=conversation.id,
    )
    serialized = _serialize_conversation_detail(context)
    answer_message = next(
        message for message in serialized.messages if message.id == assistant_message.id
    )
    return ChatAskResponse(conversation=serialized, answer_message=answer_message)


def delete_conversation(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> None:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
            Conversation.user_id == user_id,
        )
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    message_ids = list(
        db.scalars(
            select(Message.id).where(Message.conversation_id == conversation.id)
        )
    )
    if message_ids:
        db.execute(
            delete(MessageCitation).where(MessageCitation.message_id.in_(message_ids))
        )
        db.execute(delete(Message).where(Message.id.in_(message_ids)))

    db.execute(delete(Conversation).where(Conversation.id == conversation.id))
    db.commit()


def _resolve_or_create_conversation(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    question: str,
    conversation_id: uuid.UUID | None,
) -> Conversation:
    if conversation_id is not None:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.workspace_id == workspace_id,
                Conversation.user_id == user_id,
            )
        )
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return conversation

    conversation = Conversation(
        workspace_id=workspace_id,
        user_id=user_id,
        title=_preview_text(question, max_length=80),
    )
    db.add(conversation)
    db.flush()
    return conversation


def _load_conversation_context(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> ConversationContext:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
            Conversation.user_id == user_id,
        )
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
        )
    )
    message_ids = [message.id for message in messages]
    citations = []
    if message_ids:
        citations = list(
            db.scalars(
                select(MessageCitation).where(
                    MessageCitation.message_id.in_(message_ids)
                )
            )
        )
    document_ids = {citation.document_id for citation in citations}
    documents_by_id = (
        {
            document.id: document
            for document in db.scalars(
                select(Document).where(Document.id.in_(document_ids))
            )
        }
        if document_ids
        else {}
    )
    citations_by_message: dict[uuid.UUID, list[MessageCitation]] = {}
    for citation in citations:
        citations_by_message.setdefault(citation.message_id, []).append(citation)
    return ConversationContext(
        conversation=conversation,
        messages=messages,
        citations_by_message=citations_by_message,
        documents_by_id=documents_by_id,
    )


def _serialize_conversation_detail(context: ConversationContext) -> ConversationDetail:
    return ConversationDetail(
        id=context.conversation.id,
        title=context.conversation.title,
        created_at=context.conversation.created_at,
        updated_at=context.conversation.updated_at,
        messages=[
            MessageResponse(
                **MessageResponse.model_validate(message).model_dump(
                    exclude={"citations"}
                ),
                citations=[
                    CitationResponse(
                        id=citation.id,
                        chunk_id=citation.chunk_id,
                        document_id=citation.document_id,
                        page_number=citation.page_number,
                        quote=citation.quote,
                        relevance_score=float(citation.relevance_score)
                        if citation.relevance_score is not None
                        else None,
                        document_title=context.documents_by_id[
                            citation.document_id
                        ].title,
                    )
                    for citation in context.citations_by_message.get(message.id, [])
                    if citation.document_id in context.documents_by_id
                ],
            )
            for message in context.messages
        ],
    )


def _validate_citation_chunk_ids(
    *,
    cited_chunk_ids: list[str],
    retrieved_chunks,
) -> list[uuid.UUID]:
    retrieved_map = {str(chunk.chunk_id): chunk for chunk in retrieved_chunks}
    validated: list[uuid.UUID] = []
    for chunk_id in cited_chunk_ids:
        if chunk_id in retrieved_map:
            validated.append(uuid.UUID(chunk_id))
    return validated


def _persist_citations(
    db: Session,
    *,
    message_id: uuid.UUID,
    retrieved_chunks,
    validated_chunk_ids: list[uuid.UUID],
    insufficient_context: bool,
) -> list[MessageCitation]:
    if insufficient_context:
        return []

    result_map = {result.chunk_id: result for result in retrieved_chunks}
    citations: list[MessageCitation] = []
    for chunk_id in validated_chunk_ids:
        result = result_map.get(chunk_id)
        if result is None:
            continue
        citation = MessageCitation(
            message_id=message_id,
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            page_number=result.page_number,
            quote=_preview_text(result.content, max_length=260),
            relevance_score=Decimal(str(round(result.score, 6))),
        )
        db.add(citation)
        citations.append(citation)
    db.flush()
    return citations


def _preview_text(value: str | None, *, max_length: int = 120) -> str | None:
    if not value:
        return None
    trimmed = " ".join(value.split())
    if len(trimmed) <= max_length:
        return trimmed
    return f"{trimmed[: max_length - 1].rstrip()}…"
