import re
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    EvaluationQuestion,
    EvaluationResult,
    EvaluationRun,
    EvaluationSet,
    User,
)
from app.models.enums import WorkspaceRole
from app.schemas.evaluation import (
    EvaluationQuestionCreate,
    EvaluationQuestionResponse,
    EvaluationResultResponse,
    EvaluationRunDetail,
    EvaluationRunSummary,
    EvaluationSetCreateRequest,
    EvaluationSetDetail,
    EvaluationSetSummary,
)
from app.schemas.retrieval import RetrievalSearchRequest
from app.services.answers import (
    SAFE_INSUFFICIENT_CONTEXT_ANSWER,
    AnswerProviderError,
    get_answer_provider,
)
from app.services.retrieval import search_workspace_chunks

settings = get_settings()
EVALUATION_ALLOWED_ROLES = {WorkspaceRole.OWNER, WorkspaceRole.ADMIN}


def list_evaluation_sets(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    membership_role: WorkspaceRole,
) -> list[EvaluationSetSummary]:
    _require_evaluation_role(membership_role)
    evaluation_sets = list(
        db.scalars(
            select(EvaluationSet)
            .where(EvaluationSet.workspace_id == workspace_id)
            .order_by(EvaluationSet.created_at.asc())
        )
    )
    summaries: list[EvaluationSetSummary] = []
    for evaluation_set in evaluation_sets:
        question_count = db.scalar(
            select(func.count(EvaluationQuestion.id)).where(
                EvaluationQuestion.evaluation_set_id == evaluation_set.id
            )
        )
        summaries.append(
            EvaluationSetSummary(
                id=evaluation_set.id,
                name=evaluation_set.name,
                description=evaluation_set.description,
                created_at=evaluation_set.created_at,
                question_count=question_count or 0,
            )
        )
    return summaries


def create_evaluation_set(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    membership_role: WorkspaceRole,
    payload: EvaluationSetCreateRequest,
) -> EvaluationSetDetail:
    _require_evaluation_role(membership_role)

    normalized_name = payload.name.strip()
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evaluation set name is required",
        )

    if db.scalar(
        select(EvaluationSet).where(
            EvaluationSet.workspace_id == workspace_id,
            EvaluationSet.name == normalized_name,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An evaluation set with this name already exists",
        )

    evaluation_set = EvaluationSet(
        workspace_id=workspace_id,
        name=normalized_name,
        description=payload.description.strip() if payload.description else None,
    )
    db.add(evaluation_set)
    db.flush()

    for question_payload in payload.questions:
        _create_evaluation_question(
            db,
            evaluation_set_id=evaluation_set.id,
            payload=question_payload,
        )

    db.commit()
    return get_evaluation_set_detail(
        db,
        workspace_id=workspace_id,
        membership_role=membership_role,
        evaluation_set_id=evaluation_set.id,
    )


def get_evaluation_set_detail(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    membership_role: WorkspaceRole,
    evaluation_set_id: uuid.UUID,
) -> EvaluationSetDetail:
    _require_evaluation_role(membership_role)
    evaluation_set = _load_evaluation_set(
        db,
        workspace_id=workspace_id,
        evaluation_set_id=evaluation_set_id,
    )
    questions = list(
        db.scalars(
            select(EvaluationQuestion)
            .where(EvaluationQuestion.evaluation_set_id == evaluation_set.id)
            .order_by(EvaluationQuestion.created_at.asc())
        )
    )
    recent_runs = list(
        db.scalars(
            select(EvaluationRun)
            .where(EvaluationRun.evaluation_set_id == evaluation_set.id)
            .order_by(EvaluationRun.created_at.desc())
            .limit(10)
        )
    )
    return EvaluationSetDetail(
        id=evaluation_set.id,
        name=evaluation_set.name,
        description=evaluation_set.description,
        created_at=evaluation_set.created_at,
        questions=[
            EvaluationQuestionResponse.model_validate(question)
            for question in questions
        ],
        recent_runs=[EvaluationRunSummary.model_validate(run) for run in recent_runs],
    )


def run_evaluation(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    current_user: User,
    membership_role: WorkspaceRole,
    evaluation_set_id: uuid.UUID,
    top_k: int,
) -> EvaluationRunDetail:
    _require_evaluation_role(membership_role)
    evaluation_set = _load_evaluation_set(
        db,
        workspace_id=workspace_id,
        evaluation_set_id=evaluation_set_id,
    )
    questions = list(
        db.scalars(
            select(EvaluationQuestion)
            .where(EvaluationQuestion.evaluation_set_id == evaluation_set.id)
            .order_by(EvaluationQuestion.created_at.asc())
        )
    )
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evaluation set has no questions",
        )

    run = EvaluationRun(
        evaluation_set_id=evaluation_set.id,
        model_name=settings.chat_model,
        embedding_model=settings.embedding_model,
        retrieval_config={"top_k": top_k, "strategy": "hybrid"},
    )
    db.add(run)
    db.flush()

    answer_provider = get_answer_provider()
    results: list[EvaluationResult] = []

    for question in questions:
        retrieval_response = search_workspace_chunks(
            db,
            workspace_id=workspace_id,
            current_user=current_user,
            membership_role=membership_role,
            request=RetrievalSearchRequest(
                query=question.question,
                top_k=top_k,
                strategy="hybrid",
                document_ids=question.expected_document_ids,
            ),
        )
        try:
            answer_result = answer_provider.generate_answer(
                question=question.question,
                retrieved_chunks=retrieval_response.results,
            )
        except AnswerProviderError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not generate evaluation answer: {exc}",
            ) from exc

        validated_chunk_ids = _validate_retrieved_chunk_ids(
            cited_chunk_ids=answer_result.citation_chunk_ids,
            retrieved_chunk_ids=[
                result.chunk_id for result in retrieval_response.results
            ],
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
        score_value, passed, notes = _score_evaluation_result(
            answer_text=answer_text,
            insufficient_context=insufficient_context,
            expected_answer_notes=question.expected_answer_notes,
            expected_document_ids=question.expected_document_ids or [],
            retrieved_chunk_document_ids=[
                result.document_id for result in retrieval_response.results
            ],
        )
        result = EvaluationResult(
            evaluation_run_id=run.id,
            evaluation_question_id=question.id,
            generated_answer=answer_text,
            retrieved_chunk_ids=(
                [result.chunk_id for result in retrieval_response.results] or None
            ),
            score=Decimal(str(round(score_value, 6))),
            passed=passed,
            notes=notes,
        )
        db.add(result)
        results.append(result)

    run.score_summary = _build_score_summary(results)
    db.commit()
    return get_evaluation_run_detail(
        db,
        workspace_id=workspace_id,
        membership_role=membership_role,
        evaluation_run_id=run.id,
    )


def get_evaluation_run_detail(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    membership_role: WorkspaceRole,
    evaluation_run_id: uuid.UUID,
) -> EvaluationRunDetail:
    _require_evaluation_role(membership_role)
    run = db.scalar(
        select(EvaluationRun)
        .join(EvaluationSet, EvaluationSet.id == EvaluationRun.evaluation_set_id)
        .where(
            EvaluationRun.id == evaluation_run_id,
            EvaluationSet.workspace_id == workspace_id,
        )
    )
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found",
        )

    evaluation_set = db.get(EvaluationSet, run.evaluation_set_id)
    results = list(
        db.scalars(
            select(EvaluationResult)
            .where(EvaluationResult.evaluation_run_id == run.id)
            .order_by(EvaluationResult.created_at.asc())
        )
    )
    questions = {
        question.id: question
        for question in db.scalars(
            select(EvaluationQuestion).where(
                EvaluationQuestion.id.in_(
                    [result.evaluation_question_id for result in results]
                )
            )
        )
    }
    return EvaluationRunDetail(
        id=run.id,
        evaluation_set_id=run.evaluation_set_id,
        evaluation_set_name=evaluation_set.name if evaluation_set else "Unknown set",
        model_name=run.model_name,
        embedding_model=run.embedding_model,
        retrieval_config=run.retrieval_config,
        score_summary=run.score_summary,
        created_at=run.created_at,
        results=[
            EvaluationResultResponse(
                id=result.id,
                evaluation_question_id=result.evaluation_question_id,
                generated_answer=result.generated_answer,
                retrieved_chunk_ids=result.retrieved_chunk_ids,
                score=float(result.score) if result.score is not None else None,
                passed=result.passed,
                notes=result.notes,
                created_at=result.created_at,
                question=questions[result.evaluation_question_id].question,
                expected_answer_notes=questions[
                    result.evaluation_question_id
                ].expected_answer_notes,
                expected_document_ids=questions[
                    result.evaluation_question_id
                ].expected_document_ids,
            )
            for result in results
            if result.evaluation_question_id in questions
        ],
    )


def _require_evaluation_role(role: WorkspaceRole) -> None:
    if role not in EVALUATION_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to run evaluations",
        )


def _load_evaluation_set(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    evaluation_set_id: uuid.UUID,
) -> EvaluationSet:
    evaluation_set = db.scalar(
        select(EvaluationSet).where(
            EvaluationSet.id == evaluation_set_id,
            EvaluationSet.workspace_id == workspace_id,
        )
    )
    if evaluation_set is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation set not found",
        )
    return evaluation_set


def _create_evaluation_question(
    db: Session,
    *,
    evaluation_set_id: uuid.UUID,
    payload: EvaluationQuestionCreate,
) -> None:
    question_text = payload.question.strip()
    expected_notes = payload.expected_answer_notes.strip()
    if not question_text or not expected_notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Each evaluation question requires question text and expected notes",
        )

    db.add(
        EvaluationQuestion(
            evaluation_set_id=evaluation_set_id,
            question=question_text,
            expected_answer_notes=expected_notes,
            expected_document_ids=payload.expected_document_ids or None,
        )
    )


def _validate_retrieved_chunk_ids(
    *,
    cited_chunk_ids: list[str],
    retrieved_chunk_ids: list[uuid.UUID],
) -> list[uuid.UUID]:
    allowed = {str(chunk_id) for chunk_id in retrieved_chunk_ids}
    return [uuid.UUID(chunk_id) for chunk_id in cited_chunk_ids if chunk_id in allowed]


def _score_evaluation_result(
    *,
    answer_text: str,
    insufficient_context: bool,
    expected_answer_notes: str,
    expected_document_ids: list[uuid.UUID],
    retrieved_chunk_document_ids: list[uuid.UUID],
) -> tuple[float, bool, str]:
    if insufficient_context:
        return (
            0.0,
            False,
            "The answer provider reported insufficient context for this question.",
        )

    note_terms = _terms(expected_answer_notes)
    answer_terms = _terms(answer_text)
    note_overlap = 0.0
    if note_terms:
        note_overlap = len(note_terms.intersection(answer_terms)) / len(note_terms)

    document_match = 0.0
    expected_doc_set = set(expected_document_ids)
    retrieved_doc_set = set(retrieved_chunk_document_ids)
    if not expected_doc_set:
        document_match = 1.0
    elif expected_doc_set.intersection(retrieved_doc_set):
        document_match = 1.0

    score = round((note_overlap * 0.4) + (document_match * 0.6), 6)
    passed = score >= 0.6
    notes = (
        f"note_overlap={note_overlap:.2f}; "
        f"document_match={document_match:.2f}; "
        f"retrieved_documents={len(retrieved_doc_set)}"
    )
    return score, passed, notes


def _build_score_summary(results: list[EvaluationResult]) -> dict:
    total = len(results)
    passed_count = sum(1 for result in results if result.passed)
    scored_values = [
        float(result.score) for result in results if result.score is not None
    ]
    average_score = sum(scored_values) / len(scored_values) if scored_values else 0.0
    return {
        "total_questions": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "pass_rate": round((passed_count / total), 4) if total else 0.0,
        "average_score": round(average_score, 4),
    }


def _terms(text: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-zA-Z0-9$]+", text.lower())
        if len(term) > 2 or term.startswith("$")
    }
