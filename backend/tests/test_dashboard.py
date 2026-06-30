from io import BytesIO

from fastapi.testclient import TestClient

from app.db.seed import seed_demo_data
from app.main import app
from app.workers import queue as queue_service


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def workspace_headers(token: str, workspace_id: str) -> dict[str, str]:
    return {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }


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


def enable_eager_ingestion(monkeypatch) -> None:
    monkeypatch.setattr(queue_service.settings, "ingestion_queue_eager", True)


def test_dashboard_returns_workspace_summary(monkeypatch) -> None:
    seed_demo_data()
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = login_seed_user(client, email="owner@example.com")
    headers = workspace_headers(token, workspace_id)

    upload_response = client.post(
        "/documents",
        headers=headers,
        data={
            "title": "Dashboard Fresh Upload",
            "visibility": "workspace",
        },
        files={
            "file": (
                "dashboard-fresh-upload.txt",
                BytesIO(
                    b"DASHBOARD CHECK\nRefund requests must include proof of purchase."
                ),
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201

    chat_response = client.post(
        "/chat/ask",
        headers=headers,
        json={"question": "What is required for a refund request?"},
    )
    assert chat_response.status_code == 200

    sets_response = client.get("/evaluations/sets", headers=headers)
    assert sets_response.status_code == 200
    evaluation_set_id = sets_response.json()[0]["id"]

    run_response = client.post(
        "/evaluations/runs",
        headers=headers,
        json={"evaluation_set_id": evaluation_set_id, "top_k": 5},
    )
    assert run_response.status_code == 200

    response = client.get("/dashboard", headers=headers)

    assert response.status_code == 200
    assert response.headers["X-Request-Id"]
    payload = response.json()
    assert payload["document_metrics"]["total_documents"] >= 5
    assert payload["document_metrics"]["processed_documents"] >= 1
    assert payload["usage_metrics"]["total_questions"] >= 1
    assert payload["recent_questions"]
    assert payload["recent_questions"][0]["content"]
    assert payload["recent_ingestion_logs"]
    assert payload["latest_evaluation_run"] is not None
    assert payload["latest_evaluation_run"]["total_questions"] >= 10


def test_dashboard_hides_evaluation_snapshot_for_viewer() -> None:
    seed_demo_data()
    client = TestClient(app)
    token, workspace_id = login_seed_user(client, email="viewer@example.com")

    response = client.get(
        "/dashboard",
        headers=workspace_headers(token, workspace_id),
    )

    assert response.status_code == 200
    assert response.json()["latest_evaluation_run"] is None
