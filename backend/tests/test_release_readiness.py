from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.seed import seed_demo_data
from app.main import app
from app.services import answers as answer_service
from app.workers import queue as queue_service


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def workspace_headers(token: str, workspace_id: str) -> dict[str, str]:
    return {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }


def enable_eager_ingestion(monkeypatch) -> None:
    monkeypatch.setattr(queue_service.settings, "ingestion_queue_eager", True)


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


def upload_document(
    client: TestClient,
    *,
    token: str,
    workspace_id: str,
    title: str,
    content: bytes,
    visibility: str = "workspace",
) -> dict:
    response = client.post(
        "/documents",
        headers=workspace_headers(token, workspace_id),
        data={"title": title, "visibility": visibility},
        files={
            "file": (
                f"{title.lower().replace(' ', '-')}.txt",
                BytesIO(content),
                "text/plain",
            )
        },
    )
    assert response.status_code == 201
    return response.json()


def test_end_to_end_demo_path_returns_grounded_citation(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    unique = uuid4().hex[:8]
    register_payload = {
        "name": f"Release User {unique}",
        "email": f"release-{unique}@example.com",
        "password": "password123",
    }

    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": register_payload["email"],
            "password": register_payload["password"],
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/auth/me", headers=auth_header(token))
    assert me_response.status_code == 200
    workspace_id = me_response.json()["memberships"][0]["workspace_id"]

    upload_response = upload_document(
        client,
        token=token,
        workspace_id=workspace_id,
        title="Release Smoke Policy",
        content=(
            b"SMOKE POLICY\nA refund request must be submitted within 14 days "
            b"with proof of purchase and an unopened item."
        ),
    )
    assert upload_response["status"] == "processed"

    chat_response = client.post(
        "/chat/ask",
        headers=workspace_headers(token, workspace_id),
        json={"question": "What are the refund conditions in the smoke policy?"},
    )

    assert chat_response.status_code == 200
    payload = chat_response.json()
    assert payload["answer_message"]["role"] == "assistant"
    assert payload["answer_message"]["citations"]
    assert "refund" in payload["answer_message"]["content"].lower()


def test_viewer_chat_cannot_leak_restricted_document_content(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)
    seed_demo_data()

    client = TestClient(app)
    owner_token, workspace_id = login_seed_user(client, email="owner@example.com")
    viewer_token, viewer_workspace_id = login_seed_user(
        client,
        email="viewer@example.com",
    )
    restricted_term = f"billing-exception-secret-{uuid4().hex}"

    upload_document(
        client,
        token=owner_token,
        workspace_id=workspace_id,
        title="Restricted Billing Exception",
        content=restricted_term.encode("utf-8"),
        visibility="restricted",
    )

    viewer_response = client.post(
        "/chat/ask",
        headers=workspace_headers(viewer_token, viewer_workspace_id),
        json={"question": restricted_term},
    )
    assert viewer_response.status_code == 200
    viewer_payload = viewer_response.json()
    assert all(
        citation["document_title"] != "Restricted Billing Exception"
        for citation in viewer_payload["answer_message"]["citations"]
    )

    owner_response = client.post(
        "/chat/ask",
        headers=workspace_headers(owner_token, workspace_id),
        json={"question": restricted_term},
    )
    assert owner_response.status_code == 200
    assert any(
        citation["document_title"] == "Restricted Billing Exception"
        for citation in owner_response.json()["answer_message"]["citations"]
    )


def test_chat_provider_error_returns_gateway_failure(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    unique = uuid4().hex[:8]
    register_payload = {
        "name": f"Provider User {unique}",
        "email": f"provider-{unique}@example.com",
        "password": "password123",
    }
    client.post("/auth/register", json=register_payload)
    login_response = client.post(
        "/auth/login",
        json={
            "email": register_payload["email"],
            "password": register_payload["password"],
        },
    )
    token = login_response.json()["access_token"]
    workspace_id = client.get("/auth/me", headers=auth_header(token)).json()[
        "memberships"
    ][0]["workspace_id"]

    upload_document(
        client,
        token=token,
        workspace_id=workspace_id,
        title="Provider Error Policy",
        content=b"Provider error test content.",
    )

    class FailingProvider:
        def generate_answer(self, *, question: str, retrieved_chunks):
            raise answer_service.AnswerProviderError("forced chat provider failure")

    monkeypatch.setattr(
        answer_service,
        "get_answer_provider",
        lambda: FailingProvider(),
    )
    monkeypatch.setattr(
        "app.services.chat.get_answer_provider",
        lambda: FailingProvider(),
    )

    response = client.post(
        "/chat/ask",
        headers=workspace_headers(token, workspace_id),
        json={"question": "Trigger provider failure"},
    )

    assert response.status_code == 502
    assert "could not generate answer" in response.json()["detail"].lower()
