# Architecture — Grounded Document Assistant

## 1. Architectural overview

Grounded Document Assistant follows a modular full-stack architecture with a clear separation between frontend, backend, database, file storage, retrieval, and AI provider integrations.

The backend is the control plane. It validates identity, applies workspace and permission filters, manages document processing, performs retrieval, builds prompts, calls model providers, and stores results.

```text
Browser
  -> Next.js Frontend
    -> FastAPI Backend
      -> Auth Module
      -> Workspace Module
      -> Document Module
      -> Ingestion Module
      -> Retrieval Module
      -> Generation Module
      -> Evaluation Module
      -> Observability Module
    -> PostgreSQL + pgvector
    -> Local/S3-compatible File Storage
    -> Redis Queue
    -> LLM Provider
    -> Embedding Provider
```

## 2. Main components

### Frontend web app

Responsibilities:

- authentication screens;
- workspace selection;
- document upload interface;
- document list and processing status;
- chat interface with citations;
- evaluation dashboard;
- admin dashboard.

Recommended stack:

- Next.js;
- TypeScript;
- Tailwind CSS;
- shadcn/ui;
- TanStack Query.

### Backend API

Responsibilities:

- authentication and authorization;
- request validation;
- business rules;
- ingestion orchestration;
- retrieval;
- prompt construction;
- LLM calls;
- answer persistence;
- evaluation execution;
- logging and healthcheck.

Recommended stack:

- Python;
- FastAPI;
- Pydantic;
- SQLAlchemy or SQLModel;
- Alembic migrations.

### Database

Responsibilities:

- users;
- workspaces;
- memberships;
- documents;
- document versions;
- chunks;
- embeddings;
- conversations;
- messages;
- citations;
- evaluation sets and runs;
- audit and ingestion logs.

Recommended stack:

- PostgreSQL;
- pgvector extension;
- relational constraints and indexes.

### Queue and worker

Responsibilities:

- process uploaded documents asynchronously;
- extract text;
- create chunks;
- generate embeddings;
- update status;
- handle failures and retries.

Recommended stack:

- Redis;
- RQ, Celery, Dramatiq, or a simple worker for MVP.

### File storage

Responsibilities:

- store original uploaded files;
- store derived artifacts if needed;
- keep files private by default.

For local development, use local disk. For production, use S3-compatible storage.

### AI provider layer

Responsibilities:

- abstract embedding model calls;
- abstract chat completion calls;
- allow provider replacement;
- track token usage and cost when possible.

## 3. Separation of frontend, backend, and database

### Frontend must not

- call the LLM provider directly;
- access database credentials;
- decide document permissions;
- generate embeddings;
- expose private file URLs.

### Backend must

- enforce all access checks;
- scope retrieval by workspace;
- validate uploaded file type and size;
- build safe prompts;
- store citations linked to retrieved chunks.

### Database must

- preserve relational consistency;
- support efficient retrieval filters;
- make document versions traceable;
- support evaluation history.

## 4. Authentication flow

1. User logs in with email and password.
2. Backend validates credentials.
3. Backend issues an access token.
4. Frontend stores token securely according to selected implementation.
5. Each API request sends the token.
6. Backend loads the user and active workspace membership.
7. Backend applies role-based rules.

For the MVP, JWT authentication is acceptable. OAuth can be added later.

## 5. Document ingestion flow

1. User uploads a document.
2. Backend validates file type, file size, and workspace membership.
3. Backend stores the file privately.
4. Backend creates document and document version records.
5. Backend enqueues ingestion job.
6. Worker extracts text.
7. Worker splits text into chunks.
8. Worker generates embeddings.
9. Worker stores chunks and vectors.
10. Worker updates document status to processed or failed.

## 6. Question-answering flow

1. User asks a question in a workspace.
2. Backend stores the user message.
3. Backend creates a retrieval query.
4. Backend searches vector index filtered by workspace and permissions.
5. Backend runs keyword or hybrid fallback if needed.
6. Backend selects and ranks context chunks.
7. Backend builds a prompt with explicit grounding rules.
8. Backend calls the LLM provider.
9. Backend validates that citations refer to retrieved chunks.
10. Backend stores answer, citations, token usage, and logs.
11. Frontend displays the answer and source references.

## 7. Permission-aware retrieval

Every retrieval query must include:

- workspace ID;
- active user ID;
- allowed document IDs or access scope;
- active document version status.

Even in demo mode, the MVP should simulate restricted and unrestricted documents to prove that the system architecture considers data leakage risks.

## 8. Retrieval strategy

### Primary retrieval

- Use vector similarity over chunk embeddings.
- Filter before ranking whenever possible.
- Return top candidate chunks with metadata.

### Fallback retrieval

- Use PostgreSQL full-text search when vector score is weak.
- Optionally combine vector and keyword scores.
- If no source is strong enough, answer with insufficient context.

## 9. Prompting strategy

Prompt rules:

- Answer only with the retrieved context.
- Do not invent sources.
- If the context is insufficient, say so.
- Cite document title, page, and chunk reference when available.
- Keep the answer concise and business-oriented.

Prompt templates should live in a dedicated folder, not hardcoded inside controllers.

## 10. Evaluation architecture

Evaluation is not an afterthought. The MVP must include a simple golden set mechanism:

- manually created questions;
- expected source documents;
- expected answer notes;
- model response;
- retrieved chunks;
- pass/fail or score;
- notes for improvement.

This demonstrates quality awareness and makes the project stronger for technical review.

## 11. Observability

Minimum observability:

- `/health` endpoint;
- structured logs;
- ingestion logs;
- error tracking through log records;
- timing for retrieval and generation;
- token usage per answer when provider supports it.

## 12. Deployment strategy

Recommended MVP deployment:

- frontend on Vercel or similar;
- backend on Render, Railway, Fly.io, or VPS;
- PostgreSQL with pgvector on managed database or containerized VPS;
- file storage on S3-compatible service;
- environment variables configured per environment.

## 13. Technical decisions and justifications

| Decision | Justification |
|---|---|
| PostgreSQL + pgvector | Keeps relational and vector data in one system for MVP simplicity. |
| FastAPI backend | Strong fit for Python AI workflows and clean API development. |
| Next.js frontend | Marketable full-stack frontend stack with good portfolio value. |
| Hybrid retrieval | Improves answer reliability when semantic search alone is weak. |
| Source citations | Reduces hallucination risk and demonstrates grounded AI behavior. |
| Golden set evaluation | Shows maturity beyond demo-only AI usage. |
| Workspace-based access | Simulates real SaaS and business security requirements. |
