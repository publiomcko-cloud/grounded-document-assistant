# Grounded Document Assistant

A full-stack portfolio project that demonstrates an applied AI/RAG application for answering questions over uploaded documents with source citations, permission-aware access, and a basic evaluation workflow.

## Objective

Build a realistic document assistant that allows a user to upload PDFs or text documents, process them into searchable chunks, ask questions in natural language, and receive grounded answers with references to the original material.

The project is designed to be useful both as a portfolio case and as a productizable freelance offer for small and medium businesses that need to reduce repetitive support, organize internal knowledge, or search large document collections.

## Problem being solved

Small businesses and teams often have relevant information spread across PDFs, policies, manuals, catalogs, FAQs, contracts, onboarding guides, and internal procedures. Searching manually is slow, inconsistent, and hard to scale.

This application solves that problem by creating a controlled RAG pipeline:

- ingest documents;
- split and version content;
- index chunks for semantic and keyword search;
- retrieve relevant context;
- generate answers with citations;
- protect access to documents by workspace and role;
- evaluate answer quality with a small golden-question set.

## Target audience

- Small and medium businesses with repeated document-based questions.
- Support teams using internal FAQs, manuals, policies, or product catalogs.
- Freelance clients who need a fast AI assistant MVP.
- Recruiters and technical reviewers evaluating full-stack, backend, data, and applied AI skills.

## Main features

### MVP features

- User authentication.
- Workspace-based document organization.
- Document upload and metadata management.
- Ingestion pipeline with chunking and versioning.
- Vector search with keyword or hybrid fallback.
- Question answering with source citations.
- Conversation history per workspace.
- Simulated permission rules to avoid document leakage.
- Basic evaluation module using 10 to 30 golden questions.
- Admin dashboard with document status and ingestion logs.
- Public demo mode with sample documents.

### Future features

- Multi-tenant billing.
- OCR for scanned PDFs.
- Advanced role-based access control.
- Human feedback loop.
- Scheduled re-indexing.
- Integrations with Google Drive, Notion, Slack, or email.
- Model provider comparison and cost dashboard.

## Suggested technology stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- React Query or TanStack Query
- shadcn/ui or equivalent component library

### Backend

- Python FastAPI for AI and ingestion services
- Node.js/Next.js API routes only if needed for lightweight app endpoints
- REST API as the primary interface

### Database and search

- PostgreSQL
- pgvector for vector storage
- Full-text search fallback using PostgreSQL
- Prisma or SQLAlchemy/Alembic for schema management

### AI and document processing

- OpenAI-compatible LLM provider, local model provider, or configurable abstraction
- Embedding model provider abstraction
- PDF parsing library
- Chunking strategy with metadata preservation

### Infrastructure

- Docker and Docker Compose
- GitHub Actions for CI
- Cloud deployment target such as Render, Railway, Fly.io, or a VPS
- Structured logs and healthcheck endpoint

## Summarized architecture

```text
User Interface
    -> Frontend Web App
        -> Backend API
            -> Auth and Workspace Service
            -> Document Management Service
            -> Ingestion Worker
            -> Retrieval Service
            -> Answer Generation Service
            -> Evaluation Service
        -> PostgreSQL + pgvector
        -> File Storage
        -> LLM and Embedding Provider
```

## Basic run instructions

```bash
git clone <repository-url>
cd grounded-document-assistant
cp .env.example .env
docker compose up -d
```

Then run the backend:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
cd backend
alembic upgrade head
python -m app.db.seed
cd ..
uvicorn app.main:app --reload --app-dir backend --port 8000
```

In a second terminal, run the frontend:

```bash
cd frontend
npm install
npm run dev
```

In a third terminal, run the ingestion worker:

```bash
source backend/.venv/bin/activate
python -m app.workers.run
```

Local defaults:

- frontend: `http://localhost:3000`
- backend: `http://localhost:8000`
- backend healthcheck: `http://localhost:8000/health`
- PostgreSQL host port: `5433`

The detailed milestone roadmap lives in `docs/development_plan.md`.

Current backend foundation includes:

- SQLAlchemy models for the core MVP schema;
- Alembic migrations in `backend/alembic/`;
- `pgvector` enabled in PostgreSQL;
- demo seed command at `python -m app.db.seed`;
- auth endpoints at `/auth/register`, `/auth/login`, `/auth/me`;
- workspace endpoints at `/workspaces` and `/workspaces/active`;
- document endpoints at `/documents`, `/documents/{id}`, `/documents/{id}/disable`, and `/documents/{id}/retry`;
- chat endpoints at `/chat/ask`, `/chat/conversations`, and `/chat/conversations/{id}`;
- evaluation endpoints at `/evaluations/sets`, `/evaluations/runs`, and `/evaluations/runs/{id}`;
- dashboard endpoint at `/dashboard`;
- retrieval endpoint at `/retrieval/search`;
- Redis-backed ingestion worker entrypoint at `python -m app.workers.run`.
- live API smoke script at `python scripts/demo_smoke.py`.

Seeded demo credentials:

- owner: `owner@example.com`
- viewer: `viewer@example.com`
- password: `grounded-demo`

Seeded demo workspace content now includes:

- four processed sample documents across `workspace`, `restricted`, and `private` visibility;
- one golden evaluation set;
- ten seeded evaluation questions tied to the sample documents.

Current document and ingestion slice includes:

- PDF and plain text upload;
- private local file storage;
- document and version metadata records;
- document list and detail retrieval;
- Redis-backed enqueueing on upload;
- text extraction for plain text and text-based PDFs;
- deterministic chunking with previewable chunk metadata;
- embedding provider abstraction with local deterministic vectors by default;
- `pgvector` persistence for chunk embeddings;
- workspace-scoped retrieval with vector search and PostgreSQL keyword fallback;
- backend visibility filtering for `workspace`, `restricted`, and `private` documents;
- stored conversations, assistant messages, and validated citations;
- local grounded answer provider by default, with an optional OpenAI-compatible path;
- seeded golden-set evaluation runs with persisted results and score summary;
- ingestion logs and failed-job retry support;
- disable and delete actions;
- frontend documents page at `http://localhost:3000/app/documents`;
- frontend chat workspace at `http://localhost:3000/app/chat`;
- frontend evaluation workspace at `http://localhost:3000/app/evaluations`.
- frontend operational dashboard at `http://localhost:3000/app`.
- expanded backend healthcheck with PostgreSQL and Redis diagnostics.
- request ID response headers plus structured request logs including workspace ID and duration.

Current embedding configuration:

- default provider: `local`
- default model: `local-hash-1536`
- optional remote mode: set `EMBEDDING_PROVIDER=openai_compatible` and provide `EMBEDDING_API_KEY` plus `EMBEDDING_BASE_URL`

Current answer-generation configuration:

- default provider: `local`
- default model: `local-grounded-answerer`
- optional remote mode: set `LLM_PROVIDER=openai_compatible` and provide `LLM_API_KEY` plus `LLM_BASE_URL`

## Verification

Backend quality checks:

```bash
source backend/.venv/bin/activate
ruff check backend scripts
ruff format --check backend scripts
cd backend
pytest
```

Frontend quality checks:

```bash
cd frontend
npm run lint
npm run typecheck
npm run format:check
npm run build
```

Live smoke flow against a running backend plus worker:

```bash
source backend/.venv/bin/activate
python scripts/demo_smoke.py --base-url http://localhost:8000
```

That smoke path logs in with the seeded owner account, uploads a text file,
waits for ingestion, asks a grounded question, and fails if no citation is
returned.

## Roadmap

1. Create repository structure and local environment.
2. Implement authentication and workspace model.
3. Implement document upload and storage metadata.
4. Implement ingestion pipeline and chunking.
5. Add vector indexing and hybrid retrieval.
6. Implement question answering with citations.
7. Add permission simulation and security checks.
8. Add evaluation golden set module.
9. Deploy public demo with sample documents.
10. Record a short demo video and publish a case study.

## Project status

Release-readiness phase complete. The repository now includes the initial
FastAPI backend, Next.js frontend, Docker infrastructure, Alembic migrations,
the core PostgreSQL schema, demo seed support, a working JWT-based auth flow,
document upload plus metadata management, a Redis-backed ingestion worker with
chunk persistence, ingestion logs, retry support, stored chunk embeddings in
`pgvector`, a permission-aware retrieval API, a chat flow with validated
citations, a seeded evaluation workflow with persisted runs and score
summaries, a reviewer-facing dashboard with health diagnostics and recent
operational activity, and a hardened automated verification path for local
release checks.

## Known limitations

- The default local answer and embedding providers are deterministic stand-ins for local development, not production-quality model behavior.
- PDF support currently targets text-based PDFs only; scanned OCR-heavy documents are still deferred.
- The frontend does not yet include browser-level end-to-end tests such as Playwright.
- Demo screenshots and GIF assets are still deferred to the deployment and portfolio-polish milestone.

## Portfolio value

This project demonstrates:

- full-stack product thinking;
- backend API design;
- relational data modeling;
- document processing;
- vector search;
- RAG architecture;
- security-aware AI features;
- testing and evaluation;
- deployment readiness;
- documentation maturity.
