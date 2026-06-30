from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.seed import seed_demo_data
from app.db.session import SessionLocal
from app.main import app
from app.models import ChunkEmbedding, DocumentChunk
from app.services import documents as document_service
from app.services import ingestion as ingestion_service
from app.services.embeddings import EmbeddingProviderError
from app.workers import queue as queue_service


def unique_user_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "name": f"User {unique}",
        "email": f"user-{unique}@example.com",
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


def test_document_upload_list_detail_disable_and_delete_flow() -> None:
    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    headers = {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }

    upload_response = client.post(
        "/documents",
        headers=headers,
        data={
            "title": "Support FAQ",
            "description": "First uploaded document",
            "visibility": "workspace",
        },
        files={
            "file": ("faq.txt", BytesIO(b"hello from a private document"), "text/plain")
        },
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]
    assert upload_response.json()["status"] == "pending"
    assert upload_response.json()["latest_version"]["version_number"] == 1
    assert upload_response.json()["latest_version_logs"]

    list_response = client.get("/documents", headers=headers)
    assert list_response.status_code == 200
    assert any(item["id"] == document_id for item in list_response.json())

    detail_response = client.get(f"/documents/{document_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Support FAQ"
    assert len(detail_response.json()["versions"]) == 1
    assert detail_response.json()["latest_version_logs"][0]["step"] in {
        "queue",
        "processing",
        "extract",
        "chunk",
        "complete",
        "failed",
    }

    disable_response = client.patch(
        f"/documents/{document_id}/disable",
        headers=headers,
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "disabled"

    delete_response = client.delete(f"/documents/{document_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = client.get(f"/documents/{document_id}", headers=headers)
    assert missing_response.status_code == 404


def test_invalid_document_type_is_rejected() -> None:
    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    headers = {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }

    response = client.post(
        "/documents",
        headers=headers,
        data={"title": "Bad file", "visibility": "workspace"},
        files={"file": ("notes.md", BytesIO(b"# not allowed"), "text/markdown")},
    )

    assert response.status_code == 400
    assert "Only PDF and plain text files are supported" in response.json()["detail"]


def test_upload_limit_is_enforced() -> None:
    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    headers = {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }
    original_limit = document_service.settings.max_upload_mb
    document_service.settings.max_upload_mb = 1

    try:
        response = client.post(
            "/documents",
            headers=headers,
            data={"title": "Too large", "visibility": "workspace"},
            files={
                "file": (
                    "large.txt",
                    BytesIO(b"a" * (document_service.settings.max_upload_bytes + 1)),
                    "text/plain",
                )
            },
        )
    finally:
        document_service.settings.max_upload_mb = original_limit

    assert response.status_code == 400
    assert "upload limit" in response.json()["detail"]


def test_viewer_cannot_upload_documents() -> None:
    client = TestClient(app)
    seed_demo_data()
    login_response = client.post(
        "/auth/login",
        json={"email": "viewer@example.com", "password": "grounded-demo"},
    )
    token = login_response.json()["access_token"]
    me_body = client.get("/auth/me", headers=auth_header(token)).json()
    workspace_id = me_body["memberships"][0]["workspace_id"]
    headers = {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }

    response = client.post(
        "/documents",
        headers=headers,
        data={"title": "Viewer upload", "visibility": "workspace"},
        files={
            "file": (
                "viewer.txt",
                BytesIO(b"viewer should not upload"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


def test_document_ingestion_persists_chunks_embeddings_and_logs(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    headers = {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }

    response = client.post(
        "/documents",
        headers=headers,
        data={
            "title": "Refund policy",
            "visibility": "workspace",
        },
        files={
            "file": (
                "refund-policy.txt",
                BytesIO(
                    (
                        b"REFUND POLICY\n"
                        b"Customers can request a refund within 30 days of "
                        b"purchase.\n\n"
                        b"Eligibility:\n"
                        b"Items must be unused, returned with proof of purchase, and "
                        b"approved by support before payment reversal is issued.\n"
                    )
                ),
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "processed"
    assert payload["latest_version"]["extraction_status"] == "processed"
    assert payload["latest_version_chunk_count"] >= 1
    assert (
        payload["latest_version_embedding_count"]
        == payload["latest_version_chunk_count"]
    )
    assert payload["latest_version_chunk_preview"][0]["content"]
    assert "Customers can request a refund within 30 days" in (
        payload["latest_version_extracted_text"] or ""
    )
    assert any(log["step"] == "extract" for log in payload["latest_version_logs"])
    assert any(log["step"] == "chunk" for log in payload["latest_version_logs"])
    assert any(log["step"] == "embed" for log in payload["latest_version_logs"])
    assert any(log["step"] == "complete" for log in payload["latest_version_logs"])

    latest_version_id = payload["latest_version"]["id"]
    with SessionLocal() as session:
        chunk_count = session.scalar(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_version_id == latest_version_id
            )
        )
        embedding = session.scalar(
            select(ChunkEmbedding)
            .join(DocumentChunk, DocumentChunk.id == ChunkEmbedding.chunk_id)
            .where(DocumentChunk.document_version_id == latest_version_id)
            .limit(1)
        )

    assert chunk_count == payload["latest_version_chunk_count"]
    assert embedding is not None
    assert embedding.embedding_model
    assert len(embedding.embedding) == 1536


def test_embedding_failure_marks_document_failed(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    headers = {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }

    class FailingProvider:
        def embed_texts(self, texts: list[str]):
            raise EmbeddingProviderError(
                f"forced embedding failure for {len(texts)} chunks"
            )

    monkeypatch.setattr(
        ingestion_service,
        "get_embedding_provider",
        lambda: FailingProvider(),
    )

    upload_response = client.post(
        "/documents",
        headers=headers,
        data={"title": "Embedding failure", "visibility": "workspace"},
        files={
            "file": (
                "embedding-failure.txt",
                BytesIO(b"this upload should fail during embeddings"),
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201
    payload = upload_response.json()
    latest_version_id = payload["latest_version"]["id"]

    assert payload["status"] == "failed"
    assert payload["latest_version"]["extraction_status"] == "failed"
    assert payload["latest_version_chunk_count"] >= 1
    assert payload["latest_version_embedding_count"] == 0
    assert any(log["status"] == "failed" for log in payload["latest_version_logs"])

    with SessionLocal() as session:
        chunk_count = session.scalar(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_version_id == latest_version_id
            )
        )
        embedding_count = session.scalar(
            select(func.count(ChunkEmbedding.id))
            .join(DocumentChunk, DocumentChunk.id == ChunkEmbedding.chunk_id)
            .where(DocumentChunk.document_version_id == latest_version_id)
        )

    assert chunk_count == payload["latest_version_chunk_count"]
    assert embedding_count == 0


def test_failed_ingestion_can_retry(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    headers = {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }

    original_extract = ingestion_service.extract_segments_from_path

    def failing_extract(_: str) -> list[object]:
        raise ValueError("forced extraction failure")

    monkeypatch.setattr(
        ingestion_service, "extract_segments_from_path", failing_extract
    )

    upload_response = client.post(
        "/documents",
        headers=headers,
        data={"title": "Broken upload", "visibility": "workspace"},
        files={"file": ("broken.txt", BytesIO(b"will fail first"), "text/plain")},
    )

    assert upload_response.status_code == 201
    payload = upload_response.json()
    document_id = payload["id"]
    assert payload["status"] == "failed"
    assert any(log["status"] == "failed" for log in payload["latest_version_logs"])

    monkeypatch.setattr(
        ingestion_service, "extract_segments_from_path", original_extract
    )

    retry_response = client.post(
        f"/documents/{document_id}/retry",
        headers=headers,
    )

    assert retry_response.status_code == 200
    retry_payload = retry_response.json()
    assert retry_payload["status"] == "processed"
    assert retry_payload["latest_version"]["extraction_status"] == "processed"
    assert retry_payload["latest_version_chunk_count"] >= 1
