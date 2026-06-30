#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a live end-to-end smoke flow against a running "
            "Grounded Document Assistant backend."
        )
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend base URL. Default: http://localhost:8000",
    )
    parser.add_argument(
        "--email",
        default="owner@example.com",
        help="Seeded demo user email. Default: owner@example.com",
    )
    parser.add_argument(
        "--password",
        default="grounded-demo",
        help="Seeded demo user password. Default: grounded-demo",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=20.0,
        help="Max seconds to wait for ingestion to complete. Default: 20",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timeout = httpx.Timeout(30.0, connect=10.0)
    smoke_text = (
        "RELEASE READINESS POLICY\n"
        "A customer can request a refund within 21 days if proof of purchase is "
        "included and the item is unopened."
    )

    with httpx.Client(base_url=args.base_url, timeout=timeout) as client:
        token = login(client, email=args.email, password=args.password)
        workspace_id = get_workspace_id(client, token)
        headers = auth_headers(token, workspace_id)

        document_id = upload_document(
            client,
            headers=headers,
            title="Release Readiness Smoke Doc",
            content=smoke_text,
        )
        document = wait_for_document_processed(
            client,
            headers=headers,
            document_id=document_id,
            timeout_seconds=args.poll_seconds,
        )
        answer = ask_question(
            client,
            headers=headers,
            question="What are the refund conditions in the smoke test document?",
        )

    citations = answer["answer_message"].get("citations", [])
    if not citations:
        print("Smoke flow failed: no citations returned.", file=sys.stderr)
        return 1

    print("Smoke flow passed.")
    print(f"Workspace: {workspace_id}")
    print(f"Document: {document['title']} ({document['status']})")
    print(f"Answer preview: {answer['answer_message']['content'][:140]}")
    print(f"Citations: {len(citations)}")
    return 0


def login(client: httpx.Client, *, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Login succeeded but no access token was returned.")
    return token


def get_workspace_id(client: httpx.Client, token: str) -> str:
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    response.raise_for_status()
    memberships = response.json().get("memberships", [])
    if not memberships:
        raise RuntimeError("Authenticated user has no workspace memberships.")
    workspace_id = memberships[0].get("workspace_id")
    if not isinstance(workspace_id, str) or not workspace_id:
        raise RuntimeError("Workspace membership did not include a workspace_id.")
    return workspace_id


def upload_document(
    client: httpx.Client,
    *,
    headers: dict[str, str],
    title: str,
    content: str,
) -> str:
    response = client.post(
        "/documents",
        headers=headers,
        data={"title": title, "visibility": "workspace"},
        files={"file": ("release-smoke.txt", content.encode("utf-8"), "text/plain")},
    )
    response.raise_for_status()
    payload = response.json()
    document_id = payload.get("id")
    if not isinstance(document_id, str) or not document_id:
        raise RuntimeError("Upload succeeded but no document id was returned.")
    return document_id


def wait_for_document_processed(
    client: httpx.Client,
    *,
    headers: dict[str, str],
    document_id: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, Any] | None = None

    while time.monotonic() < deadline:
        response = client.get(f"/documents/{document_id}", headers=headers)
        response.raise_for_status()
        payload = response.json()
        last_payload = payload
        status = payload.get("status")
        if status == "processed":
            return payload
        if status == "failed":
            raise RuntimeError("Document ingestion failed during smoke flow.")
        time.sleep(1.0)

    raise RuntimeError(
        "Timed out waiting for document ingestion to complete. "
        f"Last payload: {last_payload}"
    )


def ask_question(
    client: httpx.Client,
    *,
    headers: dict[str, str],
    question: str,
) -> dict[str, Any]:
    response = client.post("/chat/ask", headers=headers, json={"question": question})
    response.raise_for_status()
    payload = response.json()
    answer_message = payload.get("answer_message", {})
    if answer_message.get("role") != "assistant":
        raise RuntimeError("Chat flow did not return an assistant answer.")
    return payload


def auth_headers(token: str, workspace_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Workspace-Id": workspace_id,
    }


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except httpx.HTTPError as exc:
        print(f"Smoke flow failed with HTTP error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except RuntimeError as exc:
        print(f"Smoke flow failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
