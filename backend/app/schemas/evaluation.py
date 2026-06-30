from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluationQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    expected_answer_notes: str
    expected_document_ids: list[UUID] | None
    created_at: datetime


class EvaluationSetSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    question_count: int


class EvaluationRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model_name: str
    embedding_model: str
    retrieval_config: dict
    score_summary: dict | None
    created_at: datetime


class EvaluationSetDetail(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    questions: list[EvaluationQuestionResponse]
    recent_runs: list[EvaluationRunSummary]


class EvaluationQuestionCreate(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    expected_answer_notes: str = Field(min_length=1, max_length=4000)
    expected_document_ids: list[UUID] | None = None


class EvaluationSetCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    questions: list[EvaluationQuestionCreate] = Field(min_length=1, max_length=50)


class EvaluationRunRequest(BaseModel):
    evaluation_set_id: UUID
    top_k: int = Field(default=5, ge=1, le=10)


class EvaluationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_question_id: UUID
    generated_answer: str
    retrieved_chunk_ids: list[UUID] | None
    score: float | None
    passed: bool | None
    notes: str | None
    created_at: datetime
    question: str
    expected_answer_notes: str
    expected_document_ids: list[UUID] | None


class EvaluationRunDetail(BaseModel):
    id: UUID
    evaluation_set_id: UUID
    evaluation_set_name: str
    model_name: str
    embedding_model: str
    retrieval_config: dict
    score_summary: dict | None
    created_at: datetime
    results: list[EvaluationResultResponse]
