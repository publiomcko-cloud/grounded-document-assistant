from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.seed import seed_demo_data
from app.main import app


def unique_user_payload() -> dict[str, str]:
    unique = uuid4().hex[:8]
    return {
        "name": f"User {unique}",
        "email": f"user-{unique}@example.com",
        "password": "password123",
    }


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_login_and_me_flow() -> None:
    client = TestClient(app)
    payload = unique_user_payload()

    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == 201
    assert register_response.json()["email"] == payload["email"]

    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/auth/me", headers=auth_header(token))
    assert me_response.status_code == 200
    me_body = me_response.json()
    assert me_body["email"] == payload["email"]
    assert len(me_body["memberships"]) == 1
    assert me_body["memberships"][0]["role"] == "owner"


def test_protected_endpoint_requires_authentication() -> None:
    client = TestClient(app)

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_seeded_demo_user_can_log_in() -> None:
    client = TestClient(app)
    seed_demo_data()

    response = client.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "grounded-demo",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_active_workspace_returns_current_membership_context() -> None:
    client = TestClient(app)
    payload = unique_user_payload()

    client.post("/auth/register", json=payload)
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    token = login_response.json()["access_token"]
    me_body = client.get("/auth/me", headers=auth_header(token)).json()
    workspace_id = me_body["memberships"][0]["workspace_id"]

    response = client.get(
        "/workspaces/active",
        headers={
            **auth_header(token),
            "X-Workspace-Id": workspace_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["workspace_id"] == workspace_id
    assert response.json()["role"] == "owner"


def test_active_workspace_rejects_non_member() -> None:
    client = TestClient(app)
    first_user = unique_user_payload()
    second_user = unique_user_payload()

    client.post("/auth/register", json=first_user)
    client.post("/auth/register", json=second_user)

    first_login = client.post(
        "/auth/login",
        json={"email": first_user["email"], "password": first_user["password"]},
    )
    second_login = client.post(
        "/auth/login",
        json={"email": second_user["email"], "password": second_user["password"]},
    )

    first_token = first_login.json()["access_token"]
    second_token = second_login.json()["access_token"]

    first_me = client.get("/auth/me", headers=auth_header(first_token)).json()
    first_workspace_id = first_me["memberships"][0]["workspace_id"]

    forbidden_response = client.get(
        "/workspaces/active",
        headers={
            **auth_header(second_token),
            "X-Workspace-Id": first_workspace_id,
        },
    )

    assert forbidden_response.status_code == 403
