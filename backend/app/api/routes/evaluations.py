from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies.auth import CurrentUserDep, WorkspaceContextDep
from app.db.session import DBSessionDep
from app.schemas.evaluation import (
    EvaluationRunDetail,
    EvaluationRunRequest,
    EvaluationSetCreateRequest,
    EvaluationSetDetail,
    EvaluationSetSummary,
)
from app.services.evaluations import (
    create_evaluation_set,
    get_evaluation_run_detail,
    get_evaluation_set_detail,
    list_evaluation_sets,
    run_evaluation,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/sets", response_model=list[EvaluationSetSummary])
def get_evaluation_sets(
    workspace_context: WorkspaceContextDep,
    db: DBSessionDep,
) -> list[EvaluationSetSummary]:
    return list_evaluation_sets(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        membership_role=workspace_context.membership.role,
    )


@router.post("/sets", response_model=EvaluationSetDetail)
def create_evaluation_set_route(
    payload: EvaluationSetCreateRequest,
    workspace_context: WorkspaceContextDep,
    db: DBSessionDep,
) -> EvaluationSetDetail:
    return create_evaluation_set(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        membership_role=workspace_context.membership.role,
        payload=payload,
    )


@router.get("/sets/{evaluation_set_id}", response_model=EvaluationSetDetail)
def get_evaluation_set(
    evaluation_set_id: UUID,
    workspace_context: WorkspaceContextDep,
    db: DBSessionDep,
) -> EvaluationSetDetail:
    return get_evaluation_set_detail(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        membership_role=workspace_context.membership.role,
        evaluation_set_id=evaluation_set_id,
    )


@router.post("/runs", response_model=EvaluationRunDetail)
def create_evaluation_run(
    payload: EvaluationRunRequest,
    workspace_context: WorkspaceContextDep,
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> EvaluationRunDetail:
    return run_evaluation(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        current_user=current_user,
        membership_role=workspace_context.membership.role,
        evaluation_set_id=payload.evaluation_set_id,
        top_k=payload.top_k,
    )


@router.get("/runs/{evaluation_run_id}", response_model=EvaluationRunDetail)
def get_evaluation_run(
    evaluation_run_id: UUID,
    workspace_context: WorkspaceContextDep,
    db: DBSessionDep,
) -> EvaluationRunDetail:
    return get_evaluation_run_detail(
        db,
        workspace_id=workspace_context.membership.workspace_id,
        membership_role=workspace_context.membership.role,
        evaluation_run_id=evaluation_run_id,
    )
