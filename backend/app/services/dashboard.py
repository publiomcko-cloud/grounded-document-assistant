import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Conversation,
    Document,
    DocumentVersion,
    EvaluationRun,
    EvaluationSet,
    IngestionLog,
    Message,
)
from app.models.enums import DocumentStatus, MessageRole, WorkspaceRole
from app.schemas.dashboard import (
    DashboardDocumentMetrics,
    DashboardIngestionLogEntry,
    DashboardLatestEvaluationRun,
    DashboardRecentQuestion,
    DashboardSummaryResponse,
    DashboardUsageMetrics,
)

EVALUATION_VISIBLE_ROLES = {WorkspaceRole.OWNER, WorkspaceRole.ADMIN}


def get_workspace_dashboard_summary(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    membership_role: WorkspaceRole,
) -> DashboardSummaryResponse:
    return DashboardSummaryResponse(
        document_metrics=_build_document_metrics(db, workspace_id=workspace_id),
        usage_metrics=_build_usage_metrics(
            db,
            workspace_id=workspace_id,
            user_id=user_id,
        ),
        recent_questions=_load_recent_questions(
            db,
            workspace_id=workspace_id,
            user_id=user_id,
        ),
        recent_ingestion_logs=_load_recent_ingestion_logs(
            db,
            workspace_id=workspace_id,
        ),
        latest_evaluation_run=_load_latest_evaluation_run(
            db,
            workspace_id=workspace_id,
            membership_role=membership_role,
        ),
    )


def _build_document_metrics(
    db: Session,
    *,
    workspace_id: uuid.UUID,
) -> DashboardDocumentMetrics:
    counts_by_status = {
        row[0]: row[1]
        for row in db.execute(
            select(Document.status, func.count(Document.id))
            .where(Document.workspace_id == workspace_id)
            .group_by(Document.status)
        ).all()
    }
    total_documents = sum(counts_by_status.values())
    return DashboardDocumentMetrics(
        total_documents=total_documents,
        pending_documents=counts_by_status.get(DocumentStatus.PENDING, 0),
        processing_documents=counts_by_status.get(DocumentStatus.PROCESSING, 0),
        processed_documents=counts_by_status.get(DocumentStatus.PROCESSED, 0),
        failed_documents=counts_by_status.get(DocumentStatus.FAILED, 0),
        disabled_documents=counts_by_status.get(DocumentStatus.DISABLED, 0),
    )


def _build_usage_metrics(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> DashboardUsageMetrics:
    total_conversations = db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.workspace_id == workspace_id,
            Conversation.user_id == user_id,
        )
    )
    question_rows = list(
        db.scalars(
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.user_id == user_id,
                Message.role == MessageRole.USER,
            )
        )
    )
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    for token_usage in db.scalars(
        select(Message.token_usage)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Conversation.workspace_id == workspace_id,
            Conversation.user_id == user_id,
            Message.role == MessageRole.ASSISTANT,
            Message.token_usage.is_not(None),
        )
    ):
        usage = _coerce_token_usage(token_usage)
        prompt_tokens += usage.get("prompt_tokens", 0)
        completion_tokens += usage.get("completion_tokens", 0)
        total_tokens += usage.get("total_tokens", 0)

    return DashboardUsageMetrics(
        total_conversations=total_conversations or 0,
        total_questions=len(question_rows),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def _load_recent_questions(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[DashboardRecentQuestion]:
    recent_messages = list(
        db.scalars(
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.user_id == user_id,
                Message.role == MessageRole.USER,
            )
            .order_by(Message.created_at.desc())
            .limit(5)
        )
    )
    return [
        DashboardRecentQuestion(
            id=message.id,
            conversation_id=message.conversation_id,
            content=message.content,
            created_at=message.created_at,
        )
        for message in recent_messages
    ]


def _load_recent_ingestion_logs(
    db: Session,
    *,
    workspace_id: uuid.UUID,
) -> list[DashboardIngestionLogEntry]:
    rows = db.execute(
        select(IngestionLog, DocumentVersion, Document)
        .join(
            DocumentVersion,
            DocumentVersion.id == IngestionLog.document_version_id,
        )
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(Document.workspace_id == workspace_id)
        .order_by(IngestionLog.created_at.desc())
        .limit(8)
    ).all()
    return [
        DashboardIngestionLogEntry(
            id=log.id,
            document_id=document.id,
            document_version_id=version.id,
            document_title=document.title,
            step=log.step,
            status=log.status.value,
            message=log.message,
            created_at=log.created_at,
        )
        for log, version, document in rows
    ]


def _load_latest_evaluation_run(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    membership_role: WorkspaceRole,
) -> DashboardLatestEvaluationRun | None:
    if membership_role not in EVALUATION_VISIBLE_ROLES:
        return None

    row = db.execute(
        select(EvaluationRun, EvaluationSet)
        .join(EvaluationSet, EvaluationSet.id == EvaluationRun.evaluation_set_id)
        .where(EvaluationSet.workspace_id == workspace_id)
        .order_by(EvaluationRun.created_at.desc())
        .limit(1)
    ).first()
    if row is None:
        return None

    run, evaluation_set = row
    summary = run.score_summary or {}
    return DashboardLatestEvaluationRun(
        id=run.id,
        evaluation_set_id=evaluation_set.id,
        evaluation_set_name=evaluation_set.name,
        created_at=run.created_at,
        pass_rate=_coerce_float(summary.get("pass_rate")),
        average_score=_coerce_float(summary.get("average_score")),
        passed_questions=_coerce_int(summary.get("passed_questions")),
        total_questions=_coerce_int(summary.get("total_questions")),
    )


def _coerce_token_usage(token_usage: Any) -> dict[str, int]:
    if not isinstance(token_usage, dict):
        return {}
    return {
        "prompt_tokens": _coerce_int(token_usage.get("prompt_tokens")) or 0,
        "completion_tokens": _coerce_int(token_usage.get("completion_tokens")) or 0,
        "total_tokens": _coerce_int(token_usage.get("total_tokens")) or 0,
    }


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None
