# Current State - Grounded Document Assistant

This document describes the current public portfolio state of Grounded Document Assistant.

## Public Demo

- Frontend: pending deployment
- Backend health: pending deployment
- API docs: pending deployment
- Demo video: pending recording

The planned public demo stack is Vercel for the frontend, Render for the FastAPI backend, Supabase PostgreSQL with `pgvector`, and Render Key Value for Redis-compatible health checks and queue support. The first public demo runs ingestion inline on the backend; a separate worker is a later upgrade after shared file storage exists.

## Current Stack

- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic
- Database: PostgreSQL with `pgvector`
- Queue: Redis with RQ worker
- Storage: private local filesystem storage for local development
- Authentication: email/password login with JWT access tokens
- AI providers: local deterministic providers by default, OpenAI-compatible provider paths available
- Testing: pytest, ruff, frontend lint/typecheck/build, live smoke script
- CI: GitHub Actions for backend and frontend validation
- Planned hosting: Vercel, Render, Supabase, Render Key Value

## Implemented Features

- User registration and login.
- Seeded owner and viewer demo accounts.
- Workspace membership loading and protected API routes.
- Workspace-scoped dashboard with document metrics, recent questions, ingestion activity, evaluation snapshot, and health diagnostics.
- Text and text-based PDF upload.
- Document metadata, versions, visibility, status, disable, delete, and retry actions.
- Private local file storage.
- Redis-backed ingestion queue.
- Worker-based extraction, chunking, embedding creation, and ingestion logs.
- Chunk and embedding persistence in PostgreSQL with `pgvector`.
- Permission-aware retrieval with workspace, private, restricted, and disabled-document filters.
- Vector retrieval plus PostgreSQL keyword fallback.
- Chat conversations with persisted user and assistant messages.
- Grounded answer generation with validated citations tied to retrieved chunks.
- Conversation creation and deletion.
- Seeded golden evaluation set.
- Custom evaluation set creation.
- Evaluation runs with persisted results, retrieved source IDs, scores, and summaries.
- Local smoke test for login, upload, ingestion, chat, and citations.

## Demo Users

```text
Owner
owner@example.com
grounded-demo

Viewer
viewer@example.com
grounded-demo
```

The owner can upload documents, manage documents, chat, create evaluation sets, and run evaluations. The viewer can access allowed workspace content but must not retrieve restricted/private content outside their permission scope.

## Current Validation Commands

Backend:

```bash
source backend/.venv/bin/activate
ruff check app backend scripts
ruff format --check app backend scripts
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run format:check
npm run build
```

Live smoke flow:

```bash
source backend/.venv/bin/activate
python scripts/demo_smoke.py --base-url http://127.0.0.1:8000
```

The smoke script expects PostgreSQL, Redis, the backend, and the worker to be running. It logs in with the seeded owner account, uploads a document, waits for ingestion, asks a grounded question, and fails if no citation is returned.

## Current Local Demo Flow

1. Start PostgreSQL and Redis with `docker compose up -d`.
2. Run Alembic migrations.
3. Seed demo data with `python -m app.db.seed`.
4. Start the FastAPI backend.
5. Start the RQ ingestion worker.
6. Start the Next.js frontend.
7. Sign in with the owner demo account.
8. Upload a document or use seeded demo documents.
9. Ask a question in chat and inspect citations.
10. Run or create an evaluation set.

## Current Limitations

- Public deployment is pending.
- Screenshots and demo video are pending.
- Browser E2E tests such as Playwright are not implemented yet.
- The default answer and embedding providers are deterministic local development providers, not production-quality model integrations.
- PDF support targets text-based PDFs; scanned documents require OCR work later.
- Local file storage is suitable for local development and a limited demo, but persistent public uploads need Supabase Storage or S3-compatible storage.
- The permission model demonstrates workspace, restricted, and private visibility behavior, but it is not a full enterprise access-control system.
- Render free-tier style deployment may cold start after inactivity once public deployment is added.

## Deployment Status

The project is currently local-demo ready and almost portfolio-ready, but not yet public-demo ready.

Remaining deployment work:

- add backend deployment assets;
- configure Supabase PostgreSQL and enable `pgvector`;
- configure Render Key Value and `REDIS_URL`;
- decide whether public uploads should persist across deploy restarts;
- configure Render backend service;
- configure Vercel frontend with `NEXT_PUBLIC_API_BASE_URL`;
- seed public synthetic demo data;
- validate public login, upload, ingestion, chat, citations, and evaluations;
- capture screenshots and record the demo video.

## Final Classification

Project status: Almost portfolio-ready.

Recommended next action: finish deployment assets and public hosting setup before capturing screenshots and recording the demo video.
