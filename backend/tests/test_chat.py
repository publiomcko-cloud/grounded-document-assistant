from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.main import app
from app.models import Message, MessageCitation
from app.services import answers as answer_service
from app.workers import queue as queue_service


def unique_user_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "name": f"Chat User {unique}",
        "email": f"chat-{unique}@example.com",
        "password": "password123",
    }


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_and_login(client: TestClient) -> tuple[str, str]:
    payload = unique_user_payload()
    client.post("/auth/register", json=payload)
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = login_response.json()["access_token"]
    me_body = client.get("/auth/me", headers=auth_header(token)).json()
    workspace_id = me_body["memberships"][0]["workspace_id"]
    return token, workspace_id


def enable_eager_ingestion(monkeypatch) -> None:
    monkeypatch.setattr(queue_service.settings, "ingestion_queue_eager", True)


def upload_document(
    client: TestClient,
    *,
    token: str,
    workspace_id: str,
    title: str,
    content: bytes,
) -> dict:
    response = client.post(
        "/documents",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
        data={"title": title, "visibility": "workspace"},
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


def test_chat_returns_answer_with_valid_citations(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    source_text = (
        b"RETURNS POLICY\nCustomers can request a refund within 30 days of "
        b"purchase with proof of purchase and an unused item."
    )
    upload_document(
        client,
        token=token,
        workspace_id=workspace_id,
        title="Returns Policy",
        content=source_text,
    )

    response = client.post(
        "/chat/ask",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
        json={"question": "What is required for a refund?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_message"]["role"] == "assistant"
    assert payload["answer_message"]["citations"]
    assert payload["answer_message"]["retrieval_metadata"]["retrieved_chunk_ids"]
    assert (
        payload["answer_message"]["citations"][0]["chunk_id"]
        in payload["answer_message"]["retrieval_metadata"]["retrieved_chunk_ids"]
    )

    conversation_id = payload["conversation"]["id"]
    detail_response = client.get(
        f"/chat/conversations/{conversation_id}",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
    )
    assert detail_response.status_code == 200
    assert len(detail_response.json()["messages"]) == 2

    list_response = client.get(
        "/chat/conversations",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["message_count"] == 2

    with SessionLocal() as session:
        message_count = session.scalar(select(func.count(Message.id)))
        citation_count = session.scalar(select(func.count(MessageCitation.id)))

    assert message_count >= 2
    assert citation_count >= 1


def test_chat_returns_safe_insufficient_context_when_no_results(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)

    response = client.post(
        "/chat/ask",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
        json={"question": "What is the moon made of in our documents?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_message"]["citations"] == []
    assert (
        payload["answer_message"]["content"]
        == answer_service.SAFE_INSUFFICIENT_CONTEXT_ANSWER
    )
    assert (
        payload["answer_message"]["retrieval_metadata"]["insufficient_context"] is True
    )


def test_chat_fails_closed_when_provider_returns_invalid_citations(
    monkeypatch,
) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    upload_document(
        client,
        token=token,
        workspace_id=workspace_id,
        title="Approvals Guide",
        content=b"Manager approval is required for exception handling.",
    )

    class InvalidCitationProvider:
        def generate_answer(self, *, question: str, retrieved_chunks):
            return answer_service.AnswerResult(
                answer="Manager approval is required.",
                insufficient_context=False,
                citation_chunk_ids=[str(uuid4())],
                model_name="invalid-test-provider",
                token_usage=None,
                provider="test",
            )

    monkeypatch.setattr(
        answer_service,
        "get_answer_provider",
        lambda: InvalidCitationProvider(),
    )
    monkeypatch.setattr(
        "app.services.chat.get_answer_provider",
        lambda: InvalidCitationProvider(),
    )

    response = client.post(
        "/chat/ask",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
        json={"question": "Who must approve exceptions?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_message"]["citations"] == []
    assert (
        payload["answer_message"]["content"]
        == answer_service.SAFE_INSUFFICIENT_CONTEXT_ANSWER
    )


def test_conversation_can_be_deleted(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    upload_document(
        client,
        token=token,
        workspace_id=workspace_id,
        title="Delete Conversation Policy",
        content=b"Refunds require proof of purchase.",
    )

    ask_response = client.post(
        "/chat/ask",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
        json={"question": "What is required for a refund?"},
    )
    assert ask_response.status_code == 200
    conversation_id = ask_response.json()["conversation"]["id"]

    delete_response = client.delete(
        f"/chat/conversations/{conversation_id}",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
    )
    assert delete_response.status_code == 204

    detail_response = client.get(
        f"/chat/conversations/{conversation_id}",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
    )
    assert detail_response.status_code == 404

    list_response = client.get(
        "/chat/conversations",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
    )
    assert list_response.status_code == 200
    assert all(item["id"] != conversation_id for item in list_response.json())
