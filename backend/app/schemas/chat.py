from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MessageRole


class ChatAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None


class CitationResponse(BaseModel):
    id: UUID
    chunk_id: UUID
    document_id: UUID
    page_number: int | None
    quote: str | None
    relevance_score: float | None
    document_title: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    content: str
    retrieval_metadata: dict[str, Any] | None
    model_name: str | None
    token_usage: dict[str, Any] | None
    created_at: datetime
    citations: list[CitationResponse] = []


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_preview: str | None


class ConversationDetail(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]


class ChatAskResponse(BaseModel):
    conversation: ConversationDetail
    answer_message: MessageResponse
