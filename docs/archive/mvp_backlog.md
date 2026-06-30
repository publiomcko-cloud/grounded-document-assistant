# MVP Backlog — Grounded Document Assistant

## 1. Backlog objective

This backlog turns the project concept into an implementation sequence. The goal is to build a working MVP that demonstrates business value, applied AI engineering, and portfolio-quality execution.

## 2. Execution phases

## Phase 0 — Repository and foundation

### Objective

Create the base project structure and local development environment.

### Deliverables

- Monorepo or structured repository.
- Frontend folder.
- Backend folder.
- Docker Compose for PostgreSQL, pgvector, and Redis.
- `.env.example`.
- Initial README.
- Healthcheck endpoint.

### Tasks

- Create repository structure.
- Configure Git and `.gitignore`.
- Add Docker Compose.
- Add backend skeleton.
- Add frontend skeleton.
- Add formatting and linting tools.
- Add initial CI workflow.

### Priority

Critical.

## Phase 1 — Authentication and workspace model

### Objective

Build the access foundation before adding documents and AI features.

### Deliverables

- User registration and login.
- Workspace creation or seeded demo workspace.
- Workspace membership model.
- Role-based guards.

### Tasks

- Implement user table and migrations.
- Implement password hashing.
- Implement JWT flow.
- Add login/register pages.
- Add protected route layout.
- Add workspace middleware.

### Priority

Critical.

## Phase 2 — Document upload and metadata

### Objective

Allow users to upload documents and track processing status.

### Deliverables

- Document upload API.
- Document list page.
- Document detail page.
- Private local file storage.
- Metadata records.

### Tasks

- Validate file type and size.
- Store uploaded files.
- Create document and version records.
- Add status badges.
- Add delete/disable action.
- Add upload progress UI if feasible.

### Priority

Critical.

## Phase 3 — Ingestion pipeline

### Objective

Process uploaded documents into chunks ready for retrieval.

### Deliverables

- Ingestion worker.
- Text extraction.
- Chunking strategy.
- Ingestion logs.
- Retry failed jobs.

### Tasks

- Add queue integration.
- Implement PDF text extraction.
- Implement chunk size and overlap configuration.
- Preserve page metadata when possible.
- Store chunks.
- Update document status.
- Add ingestion log UI.

### Priority

Critical.

## Phase 4 — Embeddings and vector index

### Objective

Convert chunks into searchable embeddings.

### Deliverables

- Embedding provider abstraction.
- pgvector storage.
- Vector index.
- Embedding job inside ingestion pipeline.

### Tasks

- Add embedding model configuration.
- Generate embeddings per chunk.
- Store model name and vector.
- Add vector index migration.
- Add embedding error handling.

### Priority

Critical.

## Phase 5 — Retrieval service

### Objective

Find relevant chunks for a user question while respecting access boundaries.

### Deliverables

- Vector search endpoint or internal service.
- Keyword fallback.
- Hybrid retrieval option.
- Workspace and permission filters.

### Tasks

- Implement vector similarity search.
- Add workspace filtering.
- Add document status filtering.
- Add keyword fallback.
- Return ranked chunks with metadata.
- Add tests for leakage prevention.

### Priority

Critical.

## Phase 6 — Answer generation with citations

### Objective

Generate grounded answers using retrieved chunks.

### Deliverables

- Chat interface.
- Answer generation endpoint.
- Source citations.
- Conversation history.
- Insufficient-context behavior.

### Tasks

- Implement conversation and message tables.
- Create prompt template.
- Add LLM provider abstraction.
- Validate citation references.
- Store answer and citations.
- Display citations in frontend.

### Priority

Critical.

## Phase 7 — Evaluation module

### Objective

Demonstrate answer quality measurement.

### Deliverables

- Golden question set CRUD or seeded set.
- Evaluation run endpoint.
- Evaluation result storage.
- Evaluation dashboard.

### Tasks

- Create evaluation tables.
- Seed 10 to 30 questions.
- Run questions against the RAG pipeline.
- Store retrieved chunks and generated answers.
- Add simple pass/fail or score field.
- Display summary.

### Priority

High.

## Phase 8 — Admin dashboard and observability

### Objective

Make the system reviewable and operationally understandable.

### Deliverables

- Admin dashboard.
- Ingestion status summary.
- Recent questions.
- Healthcheck.
- Structured logs.

### Tasks

- Add dashboard cards.
- Add recent ingestion errors table.
- Add token usage when available.
- Add request ID logging.
- Add backend `/health` endpoint.

### Priority

High.

## Phase 9 — Deployment and portfolio polish

### Objective

Publish the project as a real portfolio asset.

### Deliverables

- Live demo.
- Demo workspace and documents.
- Public README with screenshots.
- Short demo video script.
- Case study page.

### Tasks

- Choose deployment platform.
- Configure environment variables.
- Deploy database and backend.
- Deploy frontend.
- Test end-to-end demo flow.
- Record 60–120 second demo video.
- Add screenshots and known limitations.

### Priority

High.

## 3. Recommended implementation sequence

1. Repository foundation.
2. Backend healthcheck.
3. Database migrations.
4. Authentication.
5. Workspace model.
6. Document upload.
7. Ingestion worker.
8. Chunk storage.
9. Embeddings.
10. Retrieval.
11. Answer generation.
12. Citations.
13. Evaluation.
14. Dashboard.
15. Deployment.

## 4. Execution risks

| Risk | Mitigation |
|---|---|
| RAG becomes only a chatbot demo | Require ingestion, retrieval, citations, evaluation, and permissions. |
| Scope grows too much | Follow MVP scope strictly. |
| PDF parsing is unreliable | Start with text-based PDFs and document OCR as future work. |
| Model provider costs increase | Add provider abstraction and token logging. |
| Citations are fabricated | Store citations only from retrieved chunks. |
| Permission leakage | Add tests that query restricted documents as unauthorized users. |

## 5. Definition of MVP completion

The MVP is complete when:

- a user can log in;
- a user can access a workspace;
- documents can be uploaded and processed;
- chunks and embeddings are stored;
- the user can ask questions;
- answers contain citations;
- access filters are applied;
- at least 10 golden questions can be evaluated;
- a public demo is deployed;
- README and setup documentation are accurate.
