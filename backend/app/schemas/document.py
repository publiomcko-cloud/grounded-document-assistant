from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    DocumentStatus,
    DocumentVisibility,
    ExtractionStatus,
    LogStatus,
)


class DocumentVersionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    file_name: str
    mime_type: str
    file_size_bytes: int
    extraction_status: ExtractionStatus
    created_at: datetime


class IngestionLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    step: str
    status: LogStatus
    message: str | None
    details: dict[str, Any] | None
    created_at: datetime


class DocumentChunkPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chunk_index: int
    page_number: int | None
    section_title: str | None
    content: str
    token_count: int | None
    created_at: datetime


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    title: str
    description: str | None
    status: DocumentStatus
    visibility: DocumentVisibility
    uploaded_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    latest_version: DocumentVersionSummary | None = None


class DocumentDetail(DocumentSummary):
    versions: list[DocumentVersionSummary]
    latest_version_logs: list[IngestionLogEntry]
    latest_version_chunk_preview: list[DocumentChunkPreview]
    latest_version_chunk_count: int
    latest_version_embedding_count: int
    latest_version_extracted_text: str | None = None
