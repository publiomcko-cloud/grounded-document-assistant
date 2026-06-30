# Instructions for Development Agent — Grounded Document Assistant

## 1. Project objective

Build a full-stack RAG application that allows users to upload documents, ask questions, and receive grounded answers with source citations. The project must demonstrate real development ability for portfolio, employment, and freelance positioning.

## 2. Product priority

The highest priority is not to create a generic chatbot. The highest priority is to create a trustworthy document assistant with:

- ingestion;
- chunking;
- retrieval;
- citations;
- permission-aware access;
- evaluation;
- deployment-ready structure.

## 3. Document hierarchy

Use the documentation in this order when making decisions:

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

If there is a conflict, prefer the MVP scope and architecture documents.

## 4. Required stack

Unless there is a strong reason to change it, use:

- Next.js and TypeScript for frontend;
- FastAPI and Python for backend;
- PostgreSQL with pgvector;
- Redis for queue support;
- Docker Compose for local infrastructure;
- provider abstraction for LLM and embeddings.

## 5. Implementation order

Implement in this sequence:

1. repository foundation;
2. Docker Compose infrastructure;
3. backend healthcheck;
4. database connection;
5. migrations;
6. authentication;
7. workspace and membership model;
8. document upload;
9. ingestion queue;
10. text extraction and chunking;
11. embeddings;
12. vector search;
13. keyword fallback;
14. chat endpoint;
15. citations;
16. frontend screens;
17. evaluation module;
18. dashboard;
19. tests;
20. deployment.

## 6. Quality rules

- Do not hardcode secrets.
- Do not call LLM providers from the frontend.
- Do not retrieve chunks without workspace filtering.
- Do not fabricate citations.
- Do not skip migrations for database changes.
- Do not implement future features before the MVP is stable.
- Keep prompts separate from controller logic.
- Add tests for critical security and retrieval behavior.
- Keep README updated as implementation evolves.

## 7. Scope rules

The MVP includes:

- authentication;
- workspace access;
- document upload;
- ingestion;
- vector search;
- keyword or hybrid fallback;
- answers with citations;
- evaluation golden set;
- dashboard;
- deployment documentation.

The MVP excludes:

- OCR;
- billing;
- Slack/Google Drive integrations;
- advanced reranking;
- streaming responses;
- mobile app;
- enterprise SSO.

Do not implement excluded features unless all MVP features are complete.

## 8. Minimum done criteria

A feature is done only when:

- backend logic exists;
- database changes are migrated;
- frontend flow exists when applicable;
- errors are handled;
- tests cover the critical path;
- documentation is updated if behavior changes.

## 9. First deliverable expected from the agent

The first implementation deliverable should include:

- repository structure;
- backend healthcheck;
- frontend skeleton;
- Docker Compose running PostgreSQL + pgvector + Redis;
- database connection proof;
- updated README commands.

## 10. Living documentation rule

When implementation diverges from documentation, update the documentation in the same pull request or commit. Documentation must remain useful for a new developer starting from zero.

## 11. Portfolio rule

Every major feature should create visible proof:

- screenshot;
- demo step;
- test result;
- README section;
- commit history;
- issue or milestone.

The final project should be understandable by a recruiter, a client, and a technical reviewer.
