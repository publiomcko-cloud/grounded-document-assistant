# Grounded Document Assistant

[![CI](https://github.com/publiomcko-cloud/grounded-document-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/publiomcko-cloud/grounded-document-assistant/actions/workflows/ci.yml)

Full-stack AI document assistant for uploading documents, processing them into searchable chunks, and answering questions with source citations.

Grounded Document Assistant is a portfolio project built to demonstrate applied RAG architecture, document ingestion, permission-aware retrieval, grounded answer generation, evaluation workflows, and full-stack product engineering. It is intended for recruiters, technical reviewers, and freelance clients evaluating practical AI application development.

## Live Portfolio Demo

- Frontend: https://grounded-document-assistant.vercel.app
- Backend health: https://grounded-document-assistant-api.onrender.com/health
- API docs: https://grounded-document-assistant-api.onrender.com/docs
- Demo video: [83-second YouTube walkthrough](https://youtu.be/uu-j3RkwNWU)

The public demo uses Vercel for the frontend, Render for the FastAPI backend, Supabase PostgreSQL with `pgvector`, and Render Key Value for Redis-compatible health checks and queue support. The first public demo runs ingestion inline on the backend; a separate worker is documented as a later upgrade after shared file storage is added.

## Demo Users

```text
Owner
owner@example.com
grounded-demo

Viewer
viewer@example.com
grounded-demo
```

The login page includes buttons that autofill these demo credentials.

## For Recruiters

This project is designed to show practical full-stack and applied AI engineering judgment, not only isolated chatbot UI. It demonstrates backend API design, relational data modeling, authentication, workspace authorization, document processing, vector retrieval, grounded citations, background jobs, evaluation workflows, and CI-backed validation.

Recommended review path:

1. Sign in with the owner demo account.
2. Open the dashboard and inspect system health, ingestion activity, and evaluation summary.
3. Upload a text document in the documents workspace and review extracted content, chunks, and logs.
4. Ask a question in chat and inspect the returned citations.
5. Create or run an evaluation set to see the repeatable quality workflow.
6. Inspect the FastAPI docs and repository documentation for architecture and trade-offs.

## For Clients

This project models how a business can turn policies, manuals, FAQs, onboarding guides, and internal procedures into a searchable assistant that answers questions with source references.

It can be adapted into solutions such as:

- internal knowledge assistants
- support-team document search
- policy and compliance assistants
- onboarding and training knowledge bases
- product manual assistants
- document-heavy customer support tools
- AI-enabled internal operations dashboards

## What It Demonstrates

- FastAPI backend with SQLAlchemy, Alembic, PostgreSQL, and `pgvector`
- Next.js App Router frontend with protected app routes
- JWT authentication and workspace membership authorization
- Document upload, private local storage, extraction, chunking, and version metadata
- Redis/RQ ingestion worker with logs and retry support
- Embedding provider abstraction with local deterministic vectors by default
- Permission-aware vector retrieval with PostgreSQL keyword fallback
- Grounded chat answers with stored conversations and validated citations
- Custom evaluation sets, seeded golden questions, evaluation runs, and score summaries
- Operational dashboard with document status, ingestion activity, recent questions, and health checks
- Backend tests, frontend lint/typecheck/build, GitHub Actions CI, and a live smoke script

## Core Demo Flow

```text
login -> dashboard -> upload document -> ingestion -> chunks/embeddings
      -> ask grounded question -> inspect citations -> run evaluation set
```

## Screenshots

| Dashboard | Documents |
| --- | --- |
| ![Dashboard overview with health and metrics](docs/screenshots/01-dashboard.png) | ![Workspace documents list and upload panel](docs/screenshots/02-documents-list.png) |

| Document Content | Chat With Citations |
| --- | --- |
| ![Document detail with extracted content and chunk preview](docs/screenshots/03-document-content.png) | ![Grounded chat answer with stored citations](docs/screenshots/04-chat-with-citations.png) |

| Evaluation Run | API Docs |
| --- | --- |
| ![Evaluation workflow and result summary](docs/screenshots/05-evaluation-run.png) | ![FastAPI documentation for backend routes](docs/screenshots/06-api-docs.png) |

| Mobile Documents |
| --- |
| ![Mobile document workspace view](docs/screenshots/07-mobile-documents.png) |

## Deployment Architecture

```text
Browser
  -> Vercel Next.js frontend
  -> Render FastAPI backend with inline ingestion
  -> Supabase PostgreSQL with pgvector
  -> Render Key Value Redis-compatible service
```

The frontend calls the backend through `NEXT_PUBLIC_API_BASE_URL`. The backend owns authentication, document APIs, retrieval, chat, evaluations, dashboard data, health checks, and first-demo inline ingestion. A separate worker can consume ingestion jobs from Redis later after uploaded files move to shared object storage.

## Local Quick Start

Create the environment file and start infrastructure:

```bash
cp .env.example .env
docker compose up -d
```

Set up the backend:

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

Run the ingestion worker in a second terminal:

```bash
source backend/.venv/bin/activate
python -m app.workers.run
```

Run the frontend in a third terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
Frontend: http://127.0.0.1:3000
Backend health: http://127.0.0.1:8000/health
API docs: http://127.0.0.1:8000/docs
Documents: http://127.0.0.1:3000/app/documents
Chat: http://127.0.0.1:3000/app/chat
Evaluations: http://127.0.0.1:3000/app/evaluations
```

PostgreSQL is exposed locally on host port `5433` to avoid common conflicts with other local PostgreSQL services.

## Environment Variables

Copy `.env.example` to `.env` for local development. Do not commit real secrets, provider tokens, customer data, or private documents.

Important local variables:

```env
DATABASE_URL=postgresql+psycopg://app:app@localhost:5433/grounded_document_assistant
REDIS_URL=redis://localhost:6379
JWT_SECRET=change-me
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
FILE_STORAGE_PATH=./storage
LLM_PROVIDER=local
EMBEDDING_PROVIDER=local
```

For public deployment, set `NEXT_PUBLIC_API_BASE_URL` in Vercel to the Render backend URL and set backend secrets in Render.

## Validation

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

Live smoke flow against a running backend plus worker:

```bash
source backend/.venv/bin/activate
python scripts/demo_smoke.py --base-url http://127.0.0.1:8000
```

The smoke script logs in with the seeded owner account, uploads a text file, waits for ingestion, asks a grounded question, and fails if no citation is returned.

## Important Endpoints

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /workspaces`
- `GET /workspaces/active`
- `POST /documents`
- `GET /documents`
- `GET /documents/{document_id}`
- `POST /documents/{document_id}/retry`
- `POST /retrieval/search`
- `POST /chat/ask`
- `GET /chat/conversations`
- `DELETE /chat/conversations/{conversation_id}`
- `GET /evaluations/sets`
- `POST /evaluations/sets`
- `POST /evaluations/runs`
- `GET /dashboard`

## Documentation

- [Changelog](CHANGELOG.md)
- [Architecture](docs/architecture.md)
- [Case study](docs/case_study.md)
- [Current state](docs/current_state.md)
- [Database modeling](docs/database_modeling.md)
- [Demo script](docs/demo_script.md)
- [Deployment](docs/deployment.md)
- [Local setup](docs/local_setup_execution.md)
- [Portfolio readiness](docs/portfolio_readiness.md)
- [Screen flows](docs/screen_flows.md)
- [Testing](docs/testing.md)
- [Test sequence](docs/test_sequence.md)

Archive:

- [Development plan](docs/archive/development_plan.md)
- [MVP backlog](docs/archive/mvp_backlog.md)
- [Instructions for agent](docs/archive/instructions_for_agent.md)

## Demo Safety

- Demo users and demo documents are synthetic.
- No private legal, medical, financial, customer, or production documents should be uploaded to the public demo.
- The default local answer and embedding providers are deterministic development providers.
- AI responses can be incomplete or wrong and should not be treated as legal, medical, financial, or professional advice.
- Public deployment should use dedicated demo credentials, synthetic documents, and non-sensitive environment values.

## Known Limitations

- The public demo is deployed, but Render free-tier services may cold start after inactivity.
- The demo video is stored as a local MP4 file in the repository; publish it to a hosted video platform later if a streamable public embed is preferred.
- Browser E2E tests such as Playwright are not implemented yet.
- PDF support targets text-based PDFs; scanned OCR-heavy documents are future work.
- File storage currently uses local disk by default.
- The default local answer and embedding providers are deterministic stand-ins for local development, not production model quality.
- Persistent public uploads require a production storage adapter such as Supabase Storage or S3-compatible storage.

## Roadmap

- Optionally publish the demo video to a hosted platform such as YouTube or Loom.
- Add Playwright browser E2E coverage.
- Add optional Supabase Storage or S3-compatible file storage.
- Add OCR support for scanned PDFs.
- Add richer retrieval evaluation and model comparison.

## License

This project is available under the [MIT License](LICENSE).
