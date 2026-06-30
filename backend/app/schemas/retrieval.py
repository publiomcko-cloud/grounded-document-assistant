from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import DocumentVisibility

RetrievalStrategy = Literal["hybrid", "vector", "keyword"]
RetrievalStrategyUsed = Literal["vector", "keyword", "keyword_fallback"]


class RetrievalSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)
    strategy: RetrievalStrategy = "hybrid"
    document_ids: list[UUID] | None = None


class RetrievalResultItem(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID
    document_title: str
    document_visibility: DocumentVisibility
    chunk_index: int
    page_number: int | None
    section_title: str | None
    content: str
    score: float
    score_type: str


class RetrievalSearchResponse(BaseModel):
    query: str
    strategy_requested: RetrievalStrategy
    strategy_used: RetrievalStrategyUsed
    total_results: int
    results: list[RetrievalResultItem]
