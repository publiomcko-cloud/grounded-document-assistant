# MVP Scope — Grounded Document Assistant

## 1. MVP objective

The MVP must prove that a business user can upload documents, ask questions, and receive grounded answers with citations while the system respects workspace boundaries and provides a basic quality evaluation workflow.

The MVP should be small enough to build quickly, but complete enough to look like a real product and a strong portfolio project.

## 2. Included features

### Authentication

Included:

- email and password login;
- JWT session;
- protected routes;
- seeded demo account.

Not required in MVP:

- OAuth;
- password reset;
- two-factor authentication.

### Workspaces and roles

Included:

- one or more workspaces;
- membership table;
- basic roles: owner, admin, member, viewer;
- backend authorization checks.

Not required in MVP:

- invitation email flow;
- billing by workspace;
- advanced organization management.

### Document upload

Included:

- PDF and plain text upload;
- file size limit;
- document title and status;
- document list page;
- disable or delete document action.

Not required in MVP:

- OCR;
- Word/Excel/PowerPoint parsing;
- batch upload;
- external storage integrations.

### Ingestion

Included:

- text extraction;
- chunking;
- chunk metadata;
- embeddings;
- processing status;
- ingestion logs.

Not required in MVP:

- complex document layout reconstruction;
- tables and image extraction;
- automatic document classification.

### Retrieval

Included:

- vector search;
- keyword fallback or hybrid search;
- workspace filtering;
- document status filtering;
- top-k configuration.

Not required in MVP:

- advanced reranking model;
- multi-query retrieval;
- graph retrieval.

### Answer generation

Included:

- question input;
- answer output;
- citations linked to chunks;
- insufficient-context response;
- conversation history.

Not required in MVP:

- voice interface;
- streaming responses;
- fine-tuned model;
- autonomous agents.

### Evaluation

Included:

- golden set with 10 to 30 questions;
- evaluation run;
- generated answer storage;
- retrieved source storage;
- basic score or pass/fail field.

Not required in MVP:

- automated LLM-as-judge scoring;
- advanced benchmark dashboards;
- continuous evaluation pipeline.

### Dashboard

Included:

- document status cards;
- recent ingestion logs;
- recent questions;
- evaluation summary.

Not required in MVP:

- full analytics suite;
- billing metrics;
- customer support module.

## 3. Scope boundaries

The system is not a general-purpose ChatGPT clone. It is a document-grounded assistant.

The assistant must not answer from general model knowledge when the user is asking about uploaded documents. If the context is insufficient, the correct behavior is to say that the available documents do not contain enough information.

## 4. Expected demo flow

1. User opens the live demo.
2. User logs in with a demo account.
3. User sees a workspace with sample documents.
4. User uploads a new PDF or uses seeded documents.
5. User waits for processing status to become complete.
6. User asks a question about the document.
7. System returns an answer with citations.
8. User opens cited source snippets.
9. Admin opens evaluation dashboard.
10. Admin runs golden question evaluation.

## 5. Done criteria

The MVP is done when:

- all included features are implemented;
- the local setup guide works from a clean environment;
- the demo can be accessed publicly;
- at least one restricted-document test passes;
- at least 10 golden questions exist;
- the README has screenshots or GIFs;
- known limitations are clearly documented.

## 6. Items that must wait

These features should not be implemented before the MVP is stable:

- OCR for scanned documents;
- multi-tenant billing;
- Slack or Google Drive integrations;
- complex admin user invitation flow;
- advanced reranking;
- streaming chat;
- mobile app;
- enterprise SSO;
- fine-tuning;
- autonomous document agents.

## 7. MVP quality bar

The MVP should be simple, but not fragile. It must include:

- clear error messages;
- empty states;
- loading states;
- validation errors;
- backend tests for critical flows;
- frontend usability good enough for a recruiter or client demo.
