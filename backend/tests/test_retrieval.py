from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.seed import seed_demo_data
from app.main import app
from app.services import retrieval as retrieval_service
from app.workers import queue as queue_service


def unique_user_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "name": f"Retrieval User {unique}",
        "email": f"retrieval-{unique}@example.com",
        "password": "password123",
    }


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def enable_eager_ingestion(monkeypatch) -> None:
    monkeypatch.setattr(queue_service.settings, "ingestion_queue_eager", True)


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
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
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


def retrieval_headers(token: str, workspace_id: str) -> dict[str, str]:
    return {
        **auth_header(token),
        "X-Workspace-Id": workspace_id,
    }


def test_vector_retrieval_returns_workspace_chunk(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    exact_query = "warranty coverage requires proof of purchase and serial number"

    upload_document(
        client,
        token=token,
        workspace_id=workspace_id,
        title="Warranty Terms",
        content=exact_query.encode("utf-8"),
    )

    response = client.post(
        "/retrieval/search",
        headers=retrieval_headers(token, workspace_id),
        json={
            "query": exact_query,
            "strategy": "vector",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy_used"] == "vector"
    assert payload["total_results"] >= 1
    assert payload["results"][0]["document_title"] == "Warranty Terms"
    assert payload["results"][0]["score_type"] == "vector_similarity"


def test_hybrid_retrieval_uses_keyword_fallback_when_vector_is_weak(
    monkeypatch,
) -> None:
    enable_eager_ingestion(monkeypatch)
    monkeypatch.setattr(retrieval_service, "VECTOR_FALLBACK_THRESHOLD", 1.1)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)

    upload_document(
        client,
        token=token,
        workspace_id=workspace_id,
        title="Refund Rules",
        content=(
            b"refunds require proof of purchase and approval from support "
            b"before payment reversal"
        ),
    )

    response = client.post(
        "/retrieval/search",
        headers=retrieval_headers(token, workspace_id),
        json={
            "query": "proof of purchase support payment reversal",
            "strategy": "hybrid",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy_used"] == "keyword_fallback"
    assert payload["total_results"] >= 1
    assert payload["results"][0]["document_title"] == "Refund Rules"


def test_workspace_filter_blocks_other_workspace_documents(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token_a, workspace_a = register_and_login(client)
    token_b, workspace_b = register_and_login(client)
    hidden_term = f"cross-workspace-secret-{uuid4().hex}"

    upload_document(
        client,
        token=token_b,
        workspace_id=workspace_b,
        title="Workspace B Secret",
        content=hidden_term.encode("utf-8"),
    )

    response = client.post(
        "/retrieval/search",
        headers=retrieval_headers(token_a, workspace_a),
        json={
            "query": hidden_term,
            "strategy": "keyword",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_results"] == 0
    assert payload["results"] == []


def test_restricted_documents_are_excluded_for_viewers(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    seed_demo_data()
    owner_token, workspace_id = login_seed_user(client, email="owner@example.com")
    viewer_token, viewer_workspace_id = login_seed_user(
        client,
        email="viewer@example.com",
    )
    restricted_term = f"restricted-only-term-{uuid4().hex}"

    upload_document(
        client,
        token=owner_token,
        workspace_id=workspace_id,
        title="Restricted Procedure",
        content=restricted_term.encode("utf-8"),
        visibility="restricted",
    )

    viewer_response = client.post(
        "/retrieval/search",
        headers=retrieval_headers(viewer_token, viewer_workspace_id),
        json={
            "query": restricted_term,
            "strategy": "keyword",
            "top_k": 3,
        },
    )

    assert viewer_response.status_code == 200
    assert viewer_response.json()["total_results"] == 0

    owner_response = client.post(
        "/retrieval/search",
        headers=retrieval_headers(owner_token, workspace_id),
        json={
            "query": restricted_term,
            "strategy": "keyword",
            "top_k": 3,
        },
    )

    assert owner_response.status_code == 200
    assert owner_response.json()["total_results"] >= 1


def test_disabled_documents_are_not_retrieved(monkeypatch) -> None:
    enable_eager_ingestion(monkeypatch)

    client = TestClient(app)
    token, workspace_id = register_and_login(client)
    hidden_term = f"disabled-doc-term-{uuid4().hex}"
    upload_payload = upload_document(
        client,
        token=token,
        workspace_id=workspace_id,
        title="Disable Me",
        content=hidden_term.encode("utf-8"),
    )

    disable_response = client.patch(
        f"/documents/{upload_payload['id']}/disable",
        headers=retrieval_headers(token, workspace_id),
    )
    assert disable_response.status_code == 200

    response = client.post(
        "/retrieval/search",
        headers=retrieval_headers(token, workspace_id),
        json={
            "query": hidden_term,
            "strategy": "keyword",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["total_results"] == 0
