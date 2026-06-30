# Test Sequence — Grounded Document Assistant

## 1. Active local services

Current running stack for this machine session on May 12, 2026:

- frontend: `http://127.0.0.1:3001`
- backend: `http://127.0.0.1:8017`
- PostgreSQL: `localhost:5433`
- Redis: `localhost:6379`
- ingestion worker: running from `python -m app.workers.run`

These alternate frontend and backend ports are in use because `3000` and `8000`
are already occupied by another local project on this machine.

## 2. Demo credentials

- owner: `owner@example.com`
- viewer: `viewer@example.com`
- password: `grounded-demo`

## 3. Fast sanity check

Run these first to confirm the stack is alive:

```bash
curl http://127.0.0.1:8017/health
curl -I http://127.0.0.1:3001
docker compose ps
```

Expected:

- backend health returns `status: ok`
- frontend returns `HTTP/1.1 200 OK`
- PostgreSQL and Redis are up

## 4. Manual test sequence

### Step 1 — Open the app

Visit:

- `http://127.0.0.1:3001`

Expected:

- landing page loads
- login and register links are visible

### Step 2 — Log in as owner

Use:

- email: `owner@example.com`
- password: `grounded-demo`

Expected:

- redirected into `/app`
- dashboard loads
- workspace cards, health diagnostics, and recent activity are visible

### Step 3 — Verify dashboard health

From the dashboard, confirm:

- document metrics are shown
- PostgreSQL health is `ok`
- Redis health is `ok`
- evaluation snapshot is visible for the owner

### Step 4 — Upload a document

Open:

- `http://127.0.0.1:3001/app/documents`

Upload a `.txt` file like:

```text
REFUND TEST POLICY
Customers can request a refund within 10 days with proof of purchase.
```

Suggested metadata:

- title: `Refund Test Policy`
- visibility: `workspace`

Expected:

- upload succeeds
- document appears in the workspace list
- status progresses to `processed`
- logs include `queue`, `processing`, `extract`, `chunk`, `embed`, and `complete`

### Step 5 — Ask a grounded question

Open:

- `http://127.0.0.1:3001/app/chat`

Ask:

```text
What is the refund deadline in the test policy?
```

Expected:

- assistant answer is returned
- at least one citation is attached
- citation document title matches the uploaded file or another relevant allowed file

### Step 6 — Verify restricted-document protection

As owner:

1. Upload a new document with visibility `restricted`
2. Put a unique term in it, for example:

```text
RESTRICTED APPROVAL NOTE
Approval code restricted-alpha-4321 is internal only.
```

As viewer:

1. Sign out
2. Sign in with `viewer@example.com` / `grounded-demo`
3. Ask for `restricted-alpha-4321` in chat

Expected:

- viewer must not receive a citation to the restricted owner document
- viewer may receive the safe insufficient-context answer, or another allowed citation, but never the restricted document

### Step 7 — Run an evaluation

Log back in as owner and open:

- `http://127.0.0.1:3001/app/evaluations`

Run the seeded evaluation set.

Expected:

- evaluation run completes successfully
- results list shows pass/fail rows
- score summary appears

### Step 8 — Verify dashboard updates

Return to:

- `http://127.0.0.1:3001/app`

Expected:

- recent question appears
- ingestion feed shows the uploaded document activity
- latest evaluation snapshot reflects the new run

## 5. API test sequence

### Health

```bash
curl http://127.0.0.1:8017/health
```

### Login

```bash
curl -X POST http://127.0.0.1:8017/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@example.com","password":"grounded-demo"}'
```

Save `access_token` from the response.

### Current user

```bash
curl http://127.0.0.1:8017/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

Save the first `workspace_id`.

### Dashboard

```bash
curl http://127.0.0.1:8017/dashboard \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Workspace-Id: <WORKSPACE_ID>"
```

### Retrieval

```bash
curl -X POST http://127.0.0.1:8017/retrieval/search \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Workspace-Id: <WORKSPACE_ID>" \
  -d '{"query":"refund proof of purchase","strategy":"hybrid","top_k":3}'
```

### Chat

```bash
curl -X POST http://127.0.0.1:8017/chat/ask \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Workspace-Id: <WORKSPACE_ID>" \
  -d '{"question":"What is the refund deadline?"}'
```

### Evaluation sets

```bash
curl http://127.0.0.1:8017/evaluations/sets \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-Workspace-Id: <WORKSPACE_ID>"
```

## 6. Automated checks

### Backend

```bash
source backend/.venv/bin/activate
ruff check backend scripts
ruff format --check backend scripts
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

### Live smoke flow

```bash
source backend/.venv/bin/activate
python scripts/demo_smoke.py --base-url http://127.0.0.1:8017
```

Expected:

- login succeeds
- upload succeeds
- ingestion completes
- chat returns an answer
- at least one citation is returned

## 7. Current service processes

The services currently running for this repo session are:

- backend `uvicorn` on `127.0.0.1:8017`
- frontend `next dev` on `127.0.0.1:3001`
- ingestion worker on queue `grounded-document-assistant-ingestion`
- Docker PostgreSQL and Redis via `docker compose`

## 8. Stop sequence

If you want to stop only the infrastructure:

```bash
docker compose down
```

If you want to stop the app-layer services too, stop the running terminals for:

- `uvicorn`
- `npm run dev`
- `python -m app.workers.run`
