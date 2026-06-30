from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.seed import seed_demo_data
from app.db.session import SessionLocal
from app.main import app
from app.models import (
    EvaluationQuestion,
    EvaluationResult,
    EvaluationRun,
    EvaluationSet,
)


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login_seed_user(
    client: TestClient,
    *,
    email: str,
    password: str = "grounded-demo",
) -> tuple[str, str]:
    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    token = login_response.json()["access_token"]
    me_body = client.get("/auth/me", headers=auth_header(token)).json()
    workspace_id = me_body["memberships"][0]["workspace_id"]
    return token, workspace_id


def evaluation_headers(token: str, workspace_id: str) -> dict[str, str]:
    return {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }


def test_seeded_evaluation_run_executes_end_to_end() -> None:
    seed_demo_data()
    client = TestClient(app)
    token, workspace_id = login_seed_user(client, email="owner@example.com")

    set_response = client.get(
        "/evaluations/sets",
        headers=evaluation_headers(token, workspace_id),
    )
    assert set_response.status_code == 200
    sets = set_response.json()
    assert sets
    assert sets[0]["question_count"] >= 10

    set_detail = client.get(
        f"/evaluations/sets/{sets[0]['id']}",
        headers=evaluation_headers(token, workspace_id),
    )
    assert set_detail.status_code == 200
    assert len(set_detail.json()["questions"]) >= 10

    run_response = client.post(
        "/evaluations/runs",
        headers=evaluation_headers(token, workspace_id),
        json={"evaluation_set_id": sets[0]["id"], "top_k": 5},
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["evaluation_set_id"] == sets[0]["id"]
    assert payload["score_summary"]["total_questions"] >= 10
    assert len(payload["results"]) == payload["score_summary"]["total_questions"]
    assert payload["results"][0]["retrieved_chunk_ids"] is not None

    run_detail = client.get(
        f"/evaluations/runs/{payload['id']}",
        headers=evaluation_headers(token, workspace_id),
    )
    assert run_detail.status_code == 200
    assert run_detail.json()["score_summary"]["average_score"] >= 0

    with SessionLocal() as session:
        set_count = session.scalar(select(func.count(EvaluationSet.id)))
        question_count = session.scalar(select(func.count(EvaluationQuestion.id)))
        run_count = session.scalar(select(func.count(EvaluationRun.id)))
        result_count = session.scalar(select(func.count(EvaluationResult.id)))

    assert set_count >= 1
    assert question_count >= 10
    assert run_count >= 1
    assert result_count >= 10


def test_custom_evaluation_set_can_be_created_and_run() -> None:
    seed_demo_data()
    client = TestClient(app)
    token, workspace_id = login_seed_user(client, email="owner@example.com")
    set_name = f"Day Trading Validation {uuid4()}"

    create_response = client.post(
        "/evaluations/sets",
        headers=evaluation_headers(token, workspace_id),
        json={
            "name": set_name,
            "description": "Questions for the uploaded trading test document.",
            "questions": [
                {
                    "question": "What is a common risk model per trade?",
                    "expected_answer_notes": (
                        "Mention risking one percent or less of account equity."
                    ),
                },
                {
                    "question": "Why do day traders avoid holding overnight?",
                    "expected_answer_notes": (
                        "Mention after-hours news, earnings releases, or gap risk."
                    ),
                },
            ],
        },
    )
    assert create_response.status_code == 200
    created_set = create_response.json()
    assert created_set["name"] == set_name
    assert len(created_set["questions"]) == 2

    run_response = client.post(
        "/evaluations/runs",
        headers=evaluation_headers(token, workspace_id),
        json={"evaluation_set_id": created_set["id"], "top_k": 5},
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["evaluation_set_id"] == created_set["id"]
    assert payload["score_summary"]["total_questions"] == 2
    assert len(payload["results"]) == 2

    with SessionLocal() as session:
        created = session.scalar(
            select(EvaluationSet).where(EvaluationSet.id == created_set["id"])
        )
        created_questions = session.scalar(
            select(func.count(EvaluationQuestion.id)).where(
                EvaluationQuestion.evaluation_set_id == created_set["id"]
            )
        )

    assert created is not None
    assert created_questions == 2


def test_viewer_cannot_run_evaluations() -> None:
    seed_demo_data()
    client = TestClient(app)
    token, workspace_id = login_seed_user(client, email="viewer@example.com")

    response = client.get(
        "/evaluations/sets",
        headers=evaluation_headers(token, workspace_id),
    )

    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()
