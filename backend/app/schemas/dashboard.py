from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardDocumentMetrics(BaseModel):
    total_documents: int
    pending_documents: int
    processing_documents: int
    processed_documents: int
    failed_documents: int
    disabled_documents: int


class DashboardUsageMetrics(BaseModel):
    total_conversations: int
    total_questions: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class DashboardRecentQuestion(BaseModel):
    id: UUID
    conversation_id: UUID
    content: str
    created_at: datetime


class DashboardIngestionLogEntry(BaseModel):
    id: UUID
    document_id: UUID
    document_version_id: UUID
    document_title: str
    step: str
    status: str
    message: str | None
    created_at: datetime


class DashboardLatestEvaluationRun(BaseModel):
    id: UUID
    evaluation_set_id: UUID
    evaluation_set_name: str
    created_at: datetime
    pass_rate: float | None
    average_score: float | None
    passed_questions: int | None
    total_questions: int | None


class DashboardSummaryResponse(BaseModel):
    document_metrics: DashboardDocumentMetrics
    usage_metrics: DashboardUsageMetrics
    recent_questions: list[DashboardRecentQuestion]
    recent_ingestion_logs: list[DashboardIngestionLogEntry]
    latest_evaluation_run: DashboardLatestEvaluationRun | None
