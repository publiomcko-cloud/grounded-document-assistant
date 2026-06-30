# Development Plan — Grounded Document Assistant

## 1. Purpose

This document translates the current project documentation into an implementation plan with clear milestones, deliverables, dependencies, validation criteria, and risks.

The repository is now in the foundation and data-layer phase. The backend and frontend skeletons exist, the local Docker environment is running, and the initial database schema and seed flow are already implemented.

This plan follows the documented priority order:

1. `docs/mvp_scope.md`
2. `docs/technical_specification.md`
3. `docs/architecture.md`
4. `docs/database_modeling.md`
5. `docs/mvp_backlog.md`
6. `docs/screen_flows.md`
7. `docs/local_environment_architecture.md`
8. `docs/local_setup_execution.md`
9. `docs/testing.md`
10. `docs/deployment.md`

## 2. Product Goal

Build a full-stack, grounded document assistant that allows users to upload documents, process them into chunks and embeddings, ask questions, and receive answers with citations while respecting workspace and document access boundaries.

The MVP must prove five things:

1. documents can be ingested and indexed;
2. retrieval is grounded and permission-aware;
3. answers include citations;
4. restricted content does not leak;
5. the system is testable, deployable, and understandable as a portfolio project.

## 3. Recommended Delivery Strategy

Build the product in thin vertical slices instead of attempting the entire system at once.

The sequence should be:

1. make the local foundation reliable;
2. establish the data model and auth boundary;
3. add document lifecycle;
4. add ingestion and retrieval;
5. add answer generation and citations;
6. add evaluation and dashboard proof;
7. harden, test, and deploy.

Each milestone below has:

- objective;
- scope;
- deliverables;
- implementation tasks;
- dependencies;
- validation criteria;
- risks and notes.

## 4. Milestone Tracker

- [x] Milestone 0 — Local Foundation and Repository Bootstrap
- [x] Milestone 1 — Database Layer and Migrations
- [x] Milestone 2 — Authentication and Workspace Authorization
- [x] Milestone 3 — Document Upload and Metadata Management
- [x] Milestone 4 — Ingestion Worker and Chunking Pipeline
- [x] Milestone 5 — Embeddings and Vector Storage
- [x] Milestone 6 — Retrieval Service with Permission Filters
- [x] Milestone 7 — Answer Generation and Citation Persistence
- [x] Milestone 8 — Evaluation Workflow
- [x] Milestone 9 — Dashboard and Observability
- [x] Milestone 10 — Testing, Hardening, and Release Readiness
- [ ] Milestone 11 — Deployment and Portfolio Polish

## 5. Milestone 0 — Local Foundation and Repository Bootstrap

Status: `[x] Completed`

### Objective

Create a reliable starting point for backend, frontend, infrastructure, and developer workflow.

### Why this milestone matters

Nothing else in the system is stable until the development environment, folder structure, and service boundaries exist.

### Scope

- create backend and frontend application skeletons;
- make local infrastructure runnable;
- establish environment variable conventions;
- add a minimum healthcheck;
- prepare linting, formatting, and CI scaffolding.

### Deliverables

- `backend/` directory with FastAPI app skeleton;
- `frontend/` directory with Next.js TypeScript app skeleton;
- working `docker-compose.yml` for PostgreSQL with `pgvector` and Redis;
- root `.env.example` aligned with actual code;
- backend `GET /health` endpoint;
- frontend starter page;
- `.gitignore`, formatting, and linting setup;
- initial GitHub Actions workflow for basic checks.

### Implementation tasks

1. Create backend structure:
   - `backend/app/api`
   - `backend/app/core`
   - `backend/app/db`
   - `backend/app/models`
   - `backend/app/prompts`
   - `backend/app/services`
   - `backend/app/workers`
   - `backend/tests`
2. Create frontend structure using Next.js App Router:
   - `frontend/src/app`
   - `frontend/src/components`
   - `frontend/src/features`
   - `frontend/src/lib`
   - `frontend/src/types`
3. Add a minimal FastAPI app with `/health`.
4. Add a minimal Next.js page confirming the app is wired.
5. Review Docker Compose port bindings.
6. Add backend dependency management and frontend package setup.
7. Add lint/format/typecheck scripts for both apps.
8. Add a basic CI workflow that runs on push and pull request.

### Dependencies

- Docker available locally;
- Node.js available locally;
- Python 3.11+ available locally.

### Validation criteria

- `docker compose up -d` completes successfully;
- PostgreSQL and Redis are reachable;
- backend starts locally;
- `curl http://localhost:8000/health` returns `{"status":"ok"}`;
- frontend loads locally;
- lint commands run successfully.

### Risks and notes

- A local port conflict already exists in the current environment on `5432`.
- The simplest fix is to change the host binding to `5433:5432` or stop the conflicting container.
- This should be resolved before documenting final local run commands.

## 6. Milestone 1 — Database Layer and Migrations

Status: `[x] Completed`

### Objective

Establish the persistent data model required for authentication, document processing, retrieval, chat, citations, evaluation, and observability.

### Why this milestone matters

This project is not only a UI demo. The data model is core to traceability, permission filtering, evaluation history, and versioned ingestion.

### Scope

- configure database connection;
- enable `pgvector`;
- create migrations;
- implement the core relational schema;
- prepare seed data support.

### Deliverables

- SQLAlchemy or SQLModel setup;
- Alembic migration configuration;
- initial migration with all core tables;
- `pgvector` extension enabled;
- seed mechanism for local/demo data.

### Implementation tasks

1. Configure backend database settings from environment variables.
2. Add database session and engine setup.
3. Model the following entities:
   - users
   - workspaces
   - workspace_memberships
   - documents
   - document_versions
   - document_chunks
   - chunk_embeddings
   - conversations
   - messages
   - message_citations
   - evaluation_sets
   - evaluation_questions
   - evaluation_runs
   - evaluation_results
   - ingestion_logs
4. Add enums for:
   - workspace role
   - document status
   - document visibility
   - extraction status
   - ingestion log status
   - message role
5. Add indexes for:
   - workspace filtering
   - document status
   - visibility
   - full-text search
   - vector search
6. Add first migration and test upgrade from zero.
7. Create a small seed command for a demo workspace and user.

### Dependencies

- Milestone 0 complete;
- PostgreSQL reachable from backend.

### Validation criteria

- migrations apply cleanly to an empty database;
- schema reflects `docs/database_modeling.md`;
- seed command inserts at least one demo user and workspace;
- `pgvector` is enabled and usable.

### Risks and notes

- Avoid postponing migrations. The docs explicitly require versioned schema changes.
- Use denormalized `workspace_id` on chunks as planned to simplify secure filtering.

## 7. Milestone 2 — Authentication and Workspace Authorization

Status: `[x] Completed`

### Objective

Create the access boundary that everything else depends on.

### Why this milestone matters

The backend is the security boundary. Retrieval and document access cannot be trusted unless authentication and workspace membership are enforced first.

### Scope

- local auth with email and password;
- JWT-based access control;
- workspace membership resolution;
- role-aware authorization rules;
- frontend protected routes.

### Deliverables

- user registration endpoint;
- login endpoint;
- password hashing;
- JWT issuance and verification;
- current-user and current-workspace resolution;
- protected frontend app shell;
- seeded demo credentials.

### Implementation tasks

1. Add password hashing service.
2. Implement user creation and duplicate email prevention.
3. Implement login endpoint.
4. Issue JWT with user identity.
5. Add backend dependency for authenticated user.
6. Add workspace membership loader.
7. Add authorization helpers for roles:
   - owner
   - admin
   - member
   - viewer
8. Build login page and authenticated layout in frontend.
9. Add demo login path or seeded credentials display.

### Dependencies

- Milestone 1 complete.

### Validation criteria

- user can register;
- user can log in;
- invalid credentials fail cleanly;
- protected endpoints reject unauthenticated requests;
- user cannot act in a workspace they do not belong to.

### Risks and notes

- Keep workspace authorization in backend dependencies or service layer, not in frontend-only guards.
- Avoid overbuilding organization management in the MVP.

## 8. Milestone 3 — Document Upload and Metadata Management

Status: `[x] Completed`

### Objective

Allow users to upload documents and track them as versioned records inside a workspace.

### Why this milestone matters

Document lifecycle is the entry point of the product. Without this, there is no ingestion pipeline and no grounded retrieval.

### Scope

- upload PDF and text files;
- validate type and size;
- store files privately;
- create document and version records;
- show document status in UI.

### Deliverables

- upload API endpoint;
- private local storage path;
- document list page;
- document detail page;
- delete and disable actions;
- visible processing state in UI.

### Implementation tasks

1. Define upload constraints from configuration.
2. Implement file validation:
   - MIME type
   - extension
   - max upload size
3. Save file to private storage path.
4. Create `documents` and `document_versions` records.
5. Initialize document status as pending or processing.
6. Create documents list endpoint.
7. Create document detail endpoint.
8. Add disable and delete actions with authorization checks.
9. Build documents page and upload UI in frontend.

### Dependencies

- Milestone 2 complete.

### Validation criteria

- valid file upload succeeds;
- invalid type fails with clear error;
- oversize upload fails with clear error;
- uploaded document appears in list;
- document version record is created;
- file is not exposed publicly.

### Risks and notes

- Private storage is part of the trust model; do not expose raw uploaded paths from the frontend.
- Track logical document separately from versioned file records as planned.

## 9. Milestone 4 — Ingestion Worker and Chunking Pipeline

Status: `[x] Completed`

### Objective

Convert uploaded files into structured text chunks ready for retrieval and citation.

### Why this milestone matters

RAG quality depends heavily on extraction quality, chunking discipline, and reliable background processing.

### Scope

- asynchronous processing;
- text extraction;
- chunking with metadata;
- ingestion logs;
- failure visibility and retry.

### Deliverables

- Redis-backed queue;
- worker process;
- PDF and text extraction pipeline;
- chunk storage;
- ingestion log model usage;
- retry mechanism for failed jobs.

### Implementation tasks

1. Choose worker approach for MVP:
   - RQ
   - Dramatiq
   - Celery
   - minimal custom worker if necessary
2. Add job enqueue on upload.
3. Implement text extraction for:
   - plain text
   - PDF
4. Design chunking strategy:
   - chunk size
   - overlap
   - ordering
   - metadata preservation
5. Store chunks with:
   - document ID
   - version ID
   - workspace ID
   - page number when available
   - section title when available
6. Update statuses through lifecycle:
   - pending
   - processing
   - processed
   - failed
7. Record ingestion log events by step.
8. Add document retry endpoint and UI action.

### Dependencies

- Milestone 3 complete;
- Redis reachable from backend and worker.

### Validation criteria

- uploaded document enqueues processing;
- worker processes file asynchronously;
- chunks are stored in order;
- ingestion log entries are created;
- failed jobs are visible;
- retry path works.

### Risks and notes

- Keep the first version simple. OCR, tables, and image extraction are explicitly out of scope.
- Chunk boundaries should be deterministic so debugging and citation mapping stay manageable.

## 10. Milestone 5 — Embeddings and Vector Storage

Status: `[x] Completed`

### Objective

Create searchable vector representations for chunks and persist them in PostgreSQL.

### Why this milestone matters

Semantic retrieval is a core MVP feature and one of the strongest portfolio signals in the project.

### Scope

- embedding provider abstraction;
- vector generation per chunk;
- storage in `pgvector`;
- vector index creation;
- error handling for embedding stage.

### Deliverables

- provider abstraction for embeddings;
- chunk embedding generation in ingestion flow;
- `chunk_embeddings` persistence;
- vector index migration;
- configurable embedding model.

### Implementation tasks

1. Define embedding provider interface.
2. Implement first provider using configured API.
3. Generate embeddings for each stored chunk.
4. Persist embedding model name and vector.
5. Add vector index for search.
6. Log embedding failures clearly.
7. Capture minimal usage and timing data if available.

### Dependencies

- Milestone 4 complete.

### Validation criteria

- processed documents produce embeddings;
- vectors are stored in database;
- index exists;
- embedding failures mark ingestion appropriately.

### Risks and notes

- Keep provider abstraction narrow and replaceable.
- Avoid coupling embedding code directly to request handlers.

## 11. Milestone 6 — Retrieval Service with Permission Filters

Status: `[x] Completed`

### Objective

Retrieve relevant chunks for a user question while guaranteeing workspace and document access controls.

### Why this milestone matters

This is the most important trust boundary in the entire product. Good retrieval without secure filtering is not acceptable.

### Scope

- vector similarity search;
- keyword fallback or hybrid retrieval;
- workspace filtering;
- document visibility and status filtering;
- ranked retrieval results with metadata.

### Deliverables

- retrieval service;
- vector search query implementation;
- PostgreSQL full-text fallback;
- hybrid retrieval option;
- leakage-prevention tests.

### Implementation tasks

1. Define retrieval request contract.
2. Implement vector similarity search by workspace.
3. Filter by:
   - workspace ID
   - allowed document visibility
   - active document status
   - active document version if relevant
4. Implement keyword fallback using full-text search.
5. Add hybrid ranking or simple fallback threshold.
6. Return chunk metadata suitable for prompt and citations.
7. Add service-level tests for restricted-document leakage prevention.

### Dependencies

- Milestone 5 complete;
- auth and workspace context already working.

### Validation criteria

- relevant chunks are returned for known questions;
- disabled documents are excluded;
- unauthorized restricted documents are excluded;
- fallback search works when vector results are weak.

### Risks and notes

- Never retrieve before applying workspace filters.
- It is better to return insufficient context than to leak or over-answer.

## 12. Milestone 7 — Answer Generation and Citation Persistence

Status: `[x] Completed`

### Objective

Generate grounded answers using retrieved context and store validated citations linked to chunks.

### Why this milestone matters

This is the user-visible heart of the product. The experience must feel useful, grounded, and trustworthy.

### Scope

- question submission;
- retrieval-to-prompt flow;
- answer generation;
- insufficient-context handling;
- citations tied to chunk records;
- conversation history.

### Deliverables

- chat/question endpoint;
- LLM provider abstraction;
- prompt template(s);
- conversation/message persistence;
- citation extraction and validation;
- frontend chat screen with source references.

### Implementation tasks

1. Define chat service flow:
   - store user message
   - retrieve chunks
   - build prompt
   - call model provider
   - validate citations
   - store assistant answer
2. Create LLM provider abstraction.
3. Store prompts separately from controllers.
4. Define response format that includes:
   - answer text
   - cited sources
   - insufficient-context branch
5. Persist conversations and messages.
6. Persist citations in `message_citations`.
7. Build frontend chat screen:
   - conversation list
   - active thread
   - answer block
   - citation cards
   - source snippet drawer

### Dependencies

- Milestone 6 complete.

### Validation criteria

- user can ask a question in a workspace;
- system returns an answer using retrieved context;
- citations point to existing chunks;
- system can say it lacks enough context;
- assistant responses are stored with metadata.

### Risks and notes

- Do not fabricate citations.
- Citation validation should fail closed if references do not map to retrieved chunks.

## 13. Milestone 8 — Evaluation Workflow

Status: `[x] Completed`

### Objective

Create a lightweight but real quality evaluation loop for the RAG system.

### Why this milestone matters

Evaluation is one of the strongest differentiators between a toy demo and a serious applied AI project.

### Scope

- define or seed a golden question set;
- run evaluations against the current retrieval and answer pipeline;
- store results;
- display summary.

### Deliverables

- evaluation set model usage;
- seeded 10 to 30 golden questions;
- evaluation run endpoint or job;
- evaluation results storage;
- evaluation dashboard view.

### Implementation tasks

1. Seed a realistic golden set using demo documents.
2. Implement evaluation runner that:
   - reads each question
   - runs retrieval and answer generation
   - stores answer
   - stores retrieved chunks
   - stores pass/fail or score
3. Add simple score strategy for MVP.
4. Build evaluation page in frontend.
5. Show recent runs and summary metrics.

### Dependencies

- Milestone 7 complete.

### Validation criteria

- evaluation run executes end-to-end;
- results are persisted;
- retrieved sources are visible;
- at least 10 seeded questions exist.

### Risks and notes

- Keep scoring simple in MVP.
- The main goal is visible proof of evaluation discipline, not benchmark sophistication.

## 14. Milestone 9 — Dashboard and Observability

Status: `[x] Completed`

### Objective

Make the system understandable to a reviewer and diagnosable by a developer.

### Why this milestone matters

A portfolio reviewer should quickly understand system state, ingestion health, and usage patterns without reading the database directly.

### Scope

- workspace dashboard;
- ingestion status summary;
- recent questions;
- health diagnostics;
- structured logs.

### Deliverables

- dashboard page;
- ingestion status cards;
- recent activity widgets;
- request ID logging;
- operational metadata in logs;
- expanded healthcheck if useful.

### Implementation tasks

1. Add dashboard cards for:
   - total documents
   - processed documents
   - failed documents
   - recent questions
   - last evaluation score
2. Add recent ingestion logs table.
3. Add request ID to backend logs.
4. Log workspace ID, operation, duration, and errors.
5. Surface token usage if available from provider.
6. Optionally expand `/health` to include database and Redis checks.

### Dependencies

- Milestone 8 complete or mostly complete.

### Validation criteria

- dashboard reflects real system state;
- logs are structured enough to debug failures;
- health endpoint is meaningful.

### Risks and notes

- Observability should support debugging without leaking secrets or sensitive content.

## 15. Milestone 10 — Testing, Hardening, and Release Readiness

Status: `[x] Completed`

### Objective

Raise the MVP from feature-complete to trustworthy and demo-ready.

### Why this milestone matters

The docs set a quality bar that includes testing, permission safety, clear UX states, and deployability.

### Scope

- backend tests for critical flows;
- frontend checks;
- end-to-end sanity path if feasible;
- better error handling;
- documentation updates.

### Deliverables

- backend unit and integration tests;
- frontend lint and core checks;
- at least one end-to-end demo path if feasible;
- updated README with screenshots or GIFs;
- known limitations documented.

### Implementation tasks

1. Add backend tests for:
   - registration/login
   - protected endpoint rejection
   - workspace isolation
   - upload validation
   - ingestion success/failure path
   - retrieval filtering
   - restricted-document leakage prevention
   - answer-with-citation persistence
   - evaluation run persistence
2. Add frontend checks:
   - lint
   - typecheck
   - component tests if used
3. Add end-to-end flow if time allows:
   - login
   - upload
   - wait for processing
   - ask question
   - verify citation
4. Improve loading, empty, and error states.
5. Update README to reflect real commands and architecture.

### Dependencies

- Milestones 0 through 9 mostly complete.

### Validation criteria

- critical backend tests pass;
- at least one permission boundary test passes;
- at least one answer-with-citation test passes;
- local setup works from zero by following docs;
- README is accurate and demo-friendly.

### Risks and notes

- Prioritize leakage prevention and citation correctness over broader low-value test coverage.

## 16. Milestone 11 — Deployment and Portfolio Polish

Status: `[ ] Pending`

### Objective

Publish the project as a portfolio-quality public demo and technical case study.

### Why this milestone matters

The final value of this project depends on whether someone external can understand it, run it, and trust it quickly.

### Scope

- deploy frontend and backend;
- provision database and worker services;
- seed demo workspace and safe sample documents;
- verify production health;
- polish documentation and assets.

### Deliverables

- deployed frontend;
- deployed backend;
- production PostgreSQL with `pgvector`;
- production environment variables;
- demo workspace;
- sample documents;
- live README links and screenshots.

### Implementation tasks

1. Select deployment providers.
2. Provision production database with `pgvector`.
3. Provision Redis or equivalent worker support.
4. Configure production secrets.
5. Deploy backend.
6. Apply migrations.
7. Seed demo data.
8. Deploy frontend.
9. Validate login, upload, retrieval, and citations in production.
10. Add screenshots, GIFs, and demo instructions to README.

### Dependencies

- MVP stable locally;
- critical tests passing.

### Validation criteria

- public demo accessible;
- healthcheck passing;
- sample documents processed;
- chat returns citations;
- restricted-document behavior still works;
- evaluation run works in deployed environment.

### Risks and notes

- Only use synthetic or safe public demo documents.
- Cold starts, storage exposure, and provider costs should be documented clearly.

## 17. Cross-Cutting Technical Rules

These rules apply across all milestones.

### Security rules

- frontend must never call model providers directly;
- all retrieval must be workspace-scoped;
- document-level visibility must be enforced in backend;
- uploaded files must remain private by default;
- secrets must only come from environment variables.

### Architecture rules

- keep prompt templates separate from controllers;
- keep provider interfaces replaceable;
- keep domain modules organized and explicit;
- use migrations for all schema changes.

### Product rules

- this is not a general chatbot;
- if the system lacks evidence, it must say so;
- future features must not delay MVP completion.

### Portfolio rules

- each major feature should create visible proof:
  - test result
  - screenshot
  - demo step
  - README section

## 18. Suggested Build Order by Week or Sprint

If this is built in focused short sprints, a practical sequence is:

### Sprint 1

- Milestone 0
- Milestone 1

### Sprint 2

- Milestone 2
- Milestone 3

### Sprint 3

- Milestone 4
- Milestone 5

### Sprint 4

- Milestone 6
- Milestone 7

### Sprint 5

- Milestone 8
- Milestone 9

### Sprint 6

- Milestone 10
- Milestone 11

This can be compressed or expanded depending on available time, but the dependency order should stay roughly the same.

## 19. Immediate Next Actions

The most sensible next implementation steps are:

- [x] fix the Docker Postgres port conflict in local development;
- [x] create backend and frontend skeletons;
- [x] add backend `/health`;
- [x] configure database connection and Alembic;
- [x] create the first migration;
- [x] seed demo users and one demo workspace;
- [x] implement registration and login;
- [x] add JWT authentication and protected routes;
- [x] add workspace membership authorization guards;
- [x] implement document upload and document/version records;
- [x] add private local file storage and upload validation;
- [x] build the documents page and status UI;
- [x] implement ingestion worker and queue integration;
- [x] add text extraction and chunk creation;
- [x] persist ingestion logs and retry flow.
- [x] generate and store chunk embeddings.
- [x] implement permission-safe retrieval with vector and keyword fallback.
- [x] implement chat, grounded answers, and validated citation persistence.
- [x] seed and run the golden-set evaluation workflow.

## 20. Definition of MVP Done

The MVP should be considered done when all of the following are true:

- a user can log in;
- a user can upload a PDF or text file;
- ingestion processes the file into chunks and embeddings;
- retrieval returns permission-safe chunks;
- the user can ask a question and receive an answer with citations;
- the system can refuse when context is insufficient;
- at least one restricted-document test passes;
- at least 10 evaluation questions exist;
- a dashboard shows operational state;
- local setup works from documentation;
- the project is deployed publicly with safe demo data;
- README clearly explains setup, architecture, and demo flow.

## 21. Final Note

The highest-value success pattern for this project is not maximum feature count. It is disciplined execution of a narrow, trustworthy RAG MVP with strong architecture, visible security thinking, usable UX, and enough testing and evaluation evidence to stand out to technical reviewers and potential clients.
