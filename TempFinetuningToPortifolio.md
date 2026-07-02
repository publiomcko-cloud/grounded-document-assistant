# Temporary Fine-Tuning Plan for Portfolio Readiness

Project: Grounded Document Assistant

Reference project: `/home/publio/projetos/eCommerce` / DataPulse Commerce

Target deployment pattern: Supabase PostgreSQL + Render backend + Render Key Value + Vercel frontend

## 0. Current Position

Status as of July 2, 2026: public deployment is live, screenshots are captured, and the demo video is recorded.

Live URLs:

```text
Frontend: https://grounded-document-assistant.vercel.app
Backend health: https://grounded-document-assistant-api.onrender.com/health
API docs: https://grounded-document-assistant-api.onrender.com/docs
```

Verified:

- [x] Vercel frontend returns `200`.
- [x] Render backend `/health` returns `200`.
- [x] Render CORS allows `https://grounded-document-assistant.vercel.app`.
- [x] Vercel is using the Next.js deployment builder through `frontend/vercel.json`.
- [x] `NEXT_PUBLIC_API_BASE_URL` is set to the Render backend URL.

Current phase:

- Phase 1 through Phase 5 are complete.
- Phase 8 is complete because `docs/portfolio_readiness.md` now exists.
- Phase 6 is complete because screenshots were captured and embedded in `README.md`.
- Phase 7 is complete because the demo video was recorded into `docs/demo_video/`.
- README live links, demo script, and portfolio readiness documentation are now updated.
- The document detail layout overflow fix was applied before screenshots were captured.

Immediate next actions:

1. [x] Update `README.md` live demo links.
2. [x] Create `docs/demo_script.md`.
3. [x] Create `docs/portfolio_readiness.md`.
4. [x] Capture screenshots into `docs/screenshots/`.
5. [x] Record or plan the demo video.
6. [ ] Run final local and public validation.

## 1. Goal

This document defines the remaining work needed to move Grounded Document Assistant from a strong local MVP into a polished public portfolio project comparable to DataPulse Commerce.

The current project already has the main application behavior implemented:

- FastAPI backend
- Next.js frontend
- PostgreSQL with `pgvector`
- Redis-backed ingestion worker
- authentication and demo users
- document upload, extraction, chunking, embeddings, and retrieval
- grounded chat with citations
- workspace-aware permission checks
- dashboard
- evaluation sets and evaluation runs
- backend tests and frontend validation scripts
- local smoke test script

The missing work is mostly portfolio packaging, public demo assets, documentation cleanup, browser-level validation, and final verification.

## 2. Standard to Match

DataPulse Commerce is considered the reference standard because it includes:

- public README with live demo links near the top
- CI badge
- demo users
- recruiter positioning
- client positioning
- clear technical demonstration section
- screenshots in `docs/screenshots/`
- demo video in `docs/demo_video/`
- `docs/current_state.md`
- `docs/case_study.md`
- `docs/demo_script.md`
- `docs/portfolio_readiness.md`
- `CHANGELOG.md`
- `LICENSE`
- deployment notes for public hosting
- archived historical planning documents under `docs/archive/`
- backend Dockerfile
- frontend Dockerfile
- Render deployment file
- browser E2E tests
- production-like validation commands

Grounded Document Assistant should reach the same portfolio shape, adapted to an AI/RAG document assistant instead of an e-commerce application.

## 3. Current Gap Summary

### Completed Strengths

- [x] Project has a clear identity and useful product concept.
- [x] Main AI/RAG workflow works locally.
- [x] Auth, documents, ingestion, retrieval, chat, citations, evaluations, and dashboard exist.
- [x] Demo users exist.
- [x] Local synthetic test document exists.
- [x] Backend test coverage exists.
- [x] Frontend lint, typecheck, and build scripts exist.
- [x] GitHub Actions CI exists.
- [x] `.env.example` exists.
- [x] Local Docker Compose exists for PostgreSQL and Redis.

### Portfolio Gaps

- [x] Public frontend URL exists: `https://grounded-document-assistant.vercel.app`.
- [x] Public backend health URL exists: `https://grounded-document-assistant-api.onrender.com/health`.
- [x] Public API docs URL exists: `https://grounded-document-assistant-api.onrender.com/docs`.
- [x] Demo video recorded in `docs/demo_video/grounded-document-assistant-demo.mp4`.
- [x] Screenshots captured in `docs/screenshots/`.
- [x] `docs/current_state.md` exists.
- [x] `docs/case_study.md` exists.
- [x] `docs/demo_script.md` exists.
- [x] `docs/portfolio_readiness.md` exists.
- [x] `CHANGELOG.md` exists.
- [x] `LICENSE` exists.
- [x] `frontend/README.md` is project-specific.
- [x] Historical planning docs are archived.
- [x] README is shaped like a recruiter/client portfolio page.
- [x] Deployment docs describe the chosen Supabase + Render + Vercel path.
- [x] Backend Dockerfile exists.
- [x] Frontend Dockerfile exists.
- [x] Render deployment blueprint exists.
- [ ] No Playwright/browser E2E test.
- [x] Demo Safety section exists in README.
- [x] README live demo links point to the public URLs.
- [x] Final portfolio readiness classification exists.

## 4. Deployment Target

Use the same deployment style as DataPulse Commerce, adjusted for the extra worker and Redis dependency.

### Frontend

- Platform: Vercel
- App: Next.js frontend
- Root directory: `frontend`
- Required environment variable:
  - `NEXT_PUBLIC_API_BASE_URL=https://<render-backend-url>`

### Backend API

- Platform: Render
- Service type: web service
- Root directory: `backend`
- Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Render free tier does not support `preDeployCommand`.
- Run Alembic migrations manually from the local terminal against the Supabase database.
- Run demo seed data manually after migrations.

### Worker

- The first public demo does not use a separate worker.
- The backend uses `INGESTION_QUEUE_EAGER=true` so uploads process inline.
- A separate Render worker is a later paid/production-like upgrade after shared object storage exists.
- Future worker command:

```bash
python -m app.workers.run
```

### Database

- Platform: Supabase PostgreSQL
- Required extension:

```sql
create extension if not exists vector;
```

- Connection string should be converted to the SQLAlchemy/psycopg form:

```env
DATABASE_URL=postgresql+psycopg://...
```

### Redis

The Phase 5 deployment path uses Render Key Value for Redis-compatible connectivity.

Recommended options:

- Render Key Value for the first public demo
- Upstash Redis if you prefer an external Redis provider
- Railway Redis if a separate Redis service is acceptable

Required variable:

```env
REDIS_URL=redis://...
REDIS_HOST=
REDIS_PORT=6379
```

For Render Key Value, `REDIS_HOST` and `REDIS_PORT` are injected from the Render service. `REDIS_URL` is still useful for local development or another Redis provider.

### File Storage

Current code uses local filesystem storage through `FILE_STORAGE_PATH`.

For a public Render demo, local disk is acceptable only if documents are seeded and the demo does not depend on persistent uploads after deploy restarts.

Recommended plan:

- Short-term portfolio demo: local filesystem storage on Render with synthetic demo data and documented limitations.
- Better production-like demo: add Supabase Storage or S3-compatible storage adapter.

## 5. Phase 1 — Repository Cleanup

Objective: remove the “unfinished scaffold” feeling.

Tasks:

- [x] Replace `frontend/README.md` with a short project-specific frontend README, or remove it if the root README is authoritative.
- [x] Create `docs/archive/`.
- [x] Move historical/planning docs into `docs/archive/`:
  - [x] `docs/archive/development_plan.md`
  - [x] `docs/archive/mvp_backlog.md`
  - [x] `docs/archive/instructions_for_agent.md`
  - [x] old planning-only sections from setup docs if needed
- [ ] Keep current docs in the main `docs/` folder:
  - [x] `architecture.md`
  - [x] `database_modeling.md`
  - [x] `deployment.md`
  - [x] `testing.md`
  - [x] `current_state.md`
  - [x] `case_study.md`
  - [ ] `demo_script.md`
  - [ ] `portfolio_readiness.md`
- [x] Add `CHANGELOG.md`.
- [x] Add `LICENSE`, preferably MIT to match DataPulse Commerce.
- [x] Confirm `.gitignore` excludes local storage, logs, `.env`, venvs, and build outputs.

Acceptance criteria:

- [x] Root file list looks intentional.
- [x] No default framework README remains visible.
- [x] README links only to current docs and an archive section for historical docs.

## 6. Phase 2 — Portfolio README Rewrite

Objective: make the project understandable to a recruiter in under two minutes.

Recommended README order:

1. Project title
2. CI badge
3. one-paragraph public description
4. Live Portfolio Demo
5. Demo Users
6. For Recruiters
7. For Clients
8. What It Demonstrates
9. Core Demo Flow
10. Screenshots
11. Deployment Architecture
12. Local Quick Start
13. Validation
14. Important Endpoints
15. Documentation
16. Demo Safety
17. Known Limitations
18. Roadmap
19. License

Required README changes:

- [x] Add CI badge.
- [x] Add `Live Portfolio Demo` section near the top.
- [x] Live Portfolio Demo section now uses public URLs:

```md
## Live Portfolio Demo

- Frontend: https://grounded-document-assistant.vercel.app
- Backend health: https://grounded-document-assistant-api.onrender.com/health
- API docs: https://grounded-document-assistant-api.onrender.com/docs
- Demo video: `docs/demo_video/grounded-document-assistant-demo.mp4`
```

- [x] Replace placeholder links with the live Vercel and Render URLs.

- [x] Add demo users:

```text
Owner
owner@example.com
grounded-demo

Viewer
viewer@example.com
grounded-demo
```

- [x] Add a `For Recruiters` section focused on:
  - full-stack development
  - backend API design
  - RAG architecture
  - document processing
  - embeddings and vector search
  - permission-aware retrieval
  - citations
  - evaluation workflow
  - testing and deployment readiness

- [x] Add a `For Clients` section focused on:
  - internal document search
  - support knowledge bases
  - policy/manual assistants
  - onboarding knowledge systems
  - customer-support deflection

- [x] Add screenshots table after screenshots are captured.
- [x] Add Demo Safety section:
  - demo documents are synthetic
  - no private legal, medical, financial, or customer documents are included
  - local provider is a deterministic development stand-in
  - AI responses should not be treated as professional advice

Acceptance criteria:

- [x] README no longer reads like a build log.
- [x] README explains the project, audience, business value, and technical value quickly.
- [x] README has the same confidence and polish level as DataPulse Commerce.

## 7. Phase 3 — Current State Documentation

Create `docs/current_state.md`.

Required sections:

- [x] Public Demo
- [x] Current Stack
- [x] Implemented Features
- [x] Current Validation Commands
- [x] Demo Users
- [x] Current Limitations
- [x] Deployment Status

Suggested current stack:

- Frontend: Next.js App Router, TypeScript
- Backend: FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL, `pgvector`
- Queue: Redis + RQ worker
- AI: local deterministic provider by default, OpenAI-compatible provider path available
- Testing: pytest, ruff, Next lint/typecheck/build, smoke script
- Planned hosting: Vercel frontend, Render backend, Supabase PostgreSQL, Render Key Value

Acceptance criteria:

- [x] The document reflects actual implemented features.
- [x] Public demo links are updated from pending to the live Vercel and Render URLs.
- [x] Limitations are honest and not alarmist.

## 8. Phase 4 — Case Study

Create `docs/case_study.md`.

Required sections:

- [x] Problem
- [x] Target Users
- [x] Solution
- [x] Main Features
- [x] Architecture
- [x] AI/RAG Flow
- [x] Technical Decisions
- [x] Trade-offs
- [x] Results
- [x] Next Steps

Key points to include:

- Small teams often have answers trapped in PDFs, manuals, policies, and internal guides.
- The app turns uploaded documents into searchable, citeable knowledge.
- Workspace and visibility filters prevent obvious document leakage.
- The evaluation module shows product thinking beyond a simple chatbot.
- Local providers keep the demo free and deterministic, but real provider mode is configurable.

Acceptance criteria:

- [x] Case study is readable by non-engineers and technical reviewers.
- [x] It does not overclaim production readiness.
- [x] It distinguishes MVP/demo trade-offs from production needs.

## 9. Phase 5 — Deployment Assets

Objective: make public deployment repeatable.

Current status: complete for the first public demo. The frontend, backend health endpoint, API docs, and CORS preflight are live.

Tasks:

- [x] Add `backend/Dockerfile`.
- [x] Add `frontend/Dockerfile` only if needed for production-like local validation.
- [x] Add `render.yaml` for:
  - [x] backend web service
  - [x] Redis-compatible Render Key Value service
  - [x] optional paid ingestion worker upgrade path
  - [x] required environment variables
- [x] Update `docs/deployment.md` for Supabase + Render + Vercel.
- [x] Add Supabase setup section:
  - [x] create project
  - [x] enable `vector` extension
  - [x] copy pooled or direct database URL
  - [x] run Alembic migrations manually after Render env vars are configured
  - [x] run demo seed manually after migrations
- [x] Add Render setup section:
  - [x] backend service
  - [x] Redis/Key Value service
  - [x] optional worker service
  - [x] `DATABASE_URL`
  - [x] `REDIS_HOST` / `REDIS_PORT`
  - [x] `JWT_SECRET`
  - [x] `CORS_ORIGINS`
  - [x] provider variables if remote LLM/embedding mode is used
- [x] Add Vercel setup section:
  - [x] set root directory to `frontend`
  - [x] set `NEXT_PUBLIC_API_BASE_URL`
  - [x] deploy
- [x] Add post-deploy validation checklist:
  - [x] `/health`
  - [x] `/docs`
  - [x] owner login
  - [x] upload text document
  - [x] inline ingestion processes document
  - [x] chat returns citation
  - [x] evaluation run completes

Important decision:

- [x] Decide whether public demo supports user uploads persistently.
- [ ] If yes, implement Supabase Storage/S3 storage adapter.
- [x] If no, document that uploaded demo files may be reset by hosting restarts.

Acceptance criteria:

- [x] A reviewer can understand exactly where each service is hosted.
- [x] Deployment docs do not list unused variables as required.
- [x] Public deployment does not depend on committed secrets.
- [x] Public frontend returns `200`.
- [x] Public backend health returns `200`.
- [x] Public CORS preflight succeeds from the Vercel origin.

## 10. Phase 6 — Screenshots

Create `docs/screenshots/`.

Recommended screenshots:

- [x] `01-dashboard.png`
- [x] `02-documents-list.png`
- [x] `03-document-content.png`
- [x] `04-chat-with-citations.png`
- [x] `05-evaluation-run.png`
- [x] `06-api-docs.png`
- [x] `07-mobile-documents.png`

Screenshot rules:

- use synthetic/demo data only
- no secrets
- no private documents
- no real tokens
- crop or retake anything visually confusing
- keep filenames stable

Acceptance criteria:

- [x] README embeds screenshots in a table.
- [x] Screenshots match current UI.
- [x] Screenshots show the RAG-specific value: upload, citations, evaluation, and dashboard.

## 11. Phase 7 — Demo Video

Create `docs/demo_video/`.

Recommended video:

- title: `Grounded Document Assistant - Portfolio Demo`
- duration: 60 to 180 seconds
- format: MP4 converted from the Playwright recording; a hosted upload can be added later if desired.

Recommended flow:

```text
0-10s: What the project is
10-35s: Login and dashboard
35-65s: Upload a document and show processing/chunks
65-95s: Ask a question and inspect citations
95-120s: Run an evaluation set
120-150s: Show backend API docs and stack/deployment summary
```

Create `docs/demo_script.md` with:

- [x] voiceover script
- [x] click path
- [x] demo credentials
- [x] safety note
- [x] fallback plan if Render cold-start delays the API

Acceptance criteria:

- [x] README links the local MP4 video.
- [x] Video recording path uses public app pages and demo credentials only.
- [x] Video shows the unique value of the AI/RAG system.

## 12. Phase 8 — Portfolio Readiness Document

Create `docs/portfolio_readiness.md`.

Required format:

```md
# Portfolio Readiness - Grounded Document Assistant

## Completed

- [x] README explains the project clearly.
- [x] Demo users documented.
- [x] Local validation commands documented.

## Pending

- [x] Screenshots added.
- [x] Demo video recorded.

## Final Classification

Project status: Public-demo deployed and nearly portfolio-ready

Recommended next action:
Run final validation.
```

Acceptance criteria:

- [x] It honestly classifies the project.
- [x] It mirrors the checklist style from DataPulse Commerce.
- [x] It does not mark public-demo tasks complete before deployment exists.

## 13. Phase 9 — Testing and E2E

Current validation exists, but portfolio parity with DataPulse Commerce requires browser-level coverage.

Tasks:

- [ ] Add Playwright to frontend.
- [ ] Add `frontend/e2e/owner-login.spec.ts`.
- [ ] Add `frontend/e2e/document-chat.spec.ts` if local stack can be controlled reliably.
- [ ] Add `npm run test:e2e`.
- [ ] Add optional GitHub Actions E2E workflow using `workflow_dispatch`.
- [ ] Update `docs/testing.md`.

Minimum E2E path:

1. open frontend
2. click owner demo fill button
3. log in
4. verify dashboard loads
5. navigate to documents
6. navigate to chat
7. navigate to evaluations

Higher-value E2E path:

1. log in
2. upload test document
3. wait for processed status
4. ask a question
5. assert citation card appears

Acceptance criteria:

- [ ] `npm run test:e2e` exists.
- [ ] At least one browser E2E test passes locally.
- [ ] README validation section mentions E2E status honestly.

## 14. Phase 10 — Environment and Config Audit

Tasks:

- [ ] Compare `.env.example` against `backend/app/core/config.py`.
- [ ] Add missing variables:
  - [ ] `EMBEDDING_REQUEST_TIMEOUT_SECONDS`
  - [ ] `RETRIEVAL_TOP_K_DEFAULT`
  - [ ] `ANSWER_MAX_CITATIONS`
- [ ] Add safety warning at top of `.env.example`.
- [ ] Separate local values from production guidance.
- [ ] Ensure CORS docs mention deployed Vercel origin.
- [ ] Ensure `NEXT_PUBLIC_API_BASE_URL` is the only frontend production variable currently required.

Acceptance criteria:

- [ ] Every documented environment variable is used.
- [ ] Every required code variable is documented.
- [ ] No real secrets exist in `.env.example`.

## 15. Phase 11 — Final Code and Documentation Consistency Audit

Run these searches and resolve or document findings:

```bash
rg -n "TODO|FIXME|coming soon|not implemented|placeholder|localhost|example.com" README.md docs .github backend frontend
```

For AI/RAG-specific risk:

```bash
rg -n "fake citation|mock answer|TODO RAG|hardcoded response|placeholder model" README.md docs backend frontend
```

Expected handling:

- `localhost` is allowed in local setup docs only.
- `example.com` is allowed only for demo credentials or placeholders clearly marked as placeholders.
- local deterministic providers should be described as local demo providers, not hidden.
- any planned feature should be clearly marked future.

Acceptance criteria:

- [ ] No obsolete feature claims remain.
- [ ] API endpoints in README match backend routes.
- [ ] Commands in docs work from the directory where they are shown.
- [ ] Demo credentials work.
- [ ] Public links work after deployment.

## 16. Phase 12 — Final Validation

Run local checks:

```bash
source backend/.venv/bin/activate
ruff check app backend scripts
ruff format --check app backend scripts
cd backend
pytest
```

Run frontend checks:

```bash
cd frontend
npm run lint
npm run typecheck
npm run format:check
npm run build
```

Run smoke test with full local stack:

```bash
source backend/.venv/bin/activate
python scripts/demo_smoke.py --base-url http://127.0.0.1:8000
```

Run production-like checks after deployment:

```bash
curl https://<render-backend-url>/health
curl https://<render-backend-url>/docs
```

Acceptance criteria:

- [ ] backend tests pass
- [ ] frontend checks pass
- [ ] smoke test passes
- [ ] deployed healthcheck passes
- [ ] deployed frontend can log in
- [ ] deployed app can answer with citations
- [ ] deployed evaluation run completes

## 17. Recommended Execution Order

Use this order to avoid rework:

1. [x] Repository cleanup
2. [x] README rewrite with pending public links
3. [x] Current state doc
4. [x] Case study
5. [x] Deployment docs and Render/Vercel/Supabase files
6. [x] Deploy database, Redis-compatible service, backend, and frontend
7. [x] Seed public demo data
8. [x] Replace pending links in README
9. [x] Portfolio readiness doc
10. [x] Demo script
11. [x] Capture screenshots
12. [x] Record demo video
13. [ ] Environment/config audit
14. [ ] Add Playwright E2E
15. [ ] Final validation and changelog release

## 18. Definition of Portfolio-Ready

Mark the project portfolio-ready only when all of these are true:

- [ ] README is polished and recruiter/client friendly.
- [x] Public frontend link exists.
- [x] Public backend health link exists.
- [x] API docs link exists.
- [ ] Demo credentials work.
- [x] Screenshots exist and are linked.
- [x] Demo video exists as a repo-hosted MP4 walkthrough.
- [x] `docs/current_state.md` exists.
- [x] `docs/case_study.md` exists.
- [x] `docs/demo_script.md` exists.
- [x] `docs/portfolio_readiness.md` exists.
- [x] `CHANGELOG.md` exists.
- [x] `LICENSE` exists.
- [x] Historical docs are archived.
- [x] Deployment docs describe Supabase + Render + Vercel accurately.
- [ ] Environment docs match actual code.
- [ ] Local validation commands pass.
- [ ] Public smoke checks pass.
- [x] Known limitations are honest.
- [ ] No secrets or private documents are committed.

## 19. Current Classification

Current status: public-demo deployed, portfolio packaging in progress.

Reason:

- The core application is functional and testable.
- The Vercel frontend and Render backend are live.
- Backend health and API docs are reachable publicly.
- CORS is configured for the Vercel frontend.
- README live links, demo script, and portfolio readiness documentation are complete.
- The repository still needs browser E2E and final validation.
- Persistent uploaded file storage remains a documented limitation for the first public demo.

Recommended next action:

Run final validation.
