# Technical Specification — Grounded Document Assistant

## 1. Overview

Grounded Document Assistant is a full-stack RAG application that answers questions over uploaded documents using retrieval, generated responses, and source citations. The system focuses on a realistic business use case: allowing teams to search and ask questions about internal PDFs, policies, FAQs, manuals, and product documents.

The project must be more than a simple chatbot. It must demonstrate a complete software product: authentication, document lifecycle, ingestion pipeline, vector and keyword retrieval, answer generation, permission-aware access, evaluation, observability, and deployment.

## 2. Project objective

Create a production-inspired MVP that shows how a small business could use AI to reduce repetitive support and centralize institutional knowledge.

The system must support:

- document upload;
- document processing;
- chunk storage;
- semantic search;
- fallback keyword or hybrid search;
- question answering with citations;
- basic evaluation of answer quality;
- access boundaries by workspace and role.

## 3. Target audience

### Business audience

- Companies with many PDF policies, manuals, FAQs, or catalogs.
- Support teams that answer repeated questions.
- Small businesses that need a knowledge assistant but cannot afford a custom enterprise platform.

### Technical audience

- Recruiters evaluating applied AI, backend, and full-stack skills.
- Clients looking for a practical freelance AI solution.
- Developers reviewing architecture, testing, and deployment practices.

## 4. Problem statement

Businesses often have useful information locked in documents. Employees and customers waste time searching manually or asking the same questions repeatedly. Generic chatbots cannot safely answer from company documents unless the system retrieves the correct sources, limits document access, and cites the origin of each answer.

This project solves that problem through a controlled RAG workflow.

## 5. Functional requirements

### Authentication and users

- Users can register and log in.
- Users belong to at least one workspace.
- Roles define access level: owner, admin, member, viewer.
- Demo users may be seeded for public portfolio usage.

### Workspace management

- A workspace groups documents, users, conversations, and evaluations.
- Users cannot access documents outside their workspace.
- Admins can invite or remove users in future versions.

### Document management

- Users can upload supported documents.
- The system stores file metadata and processing status.
- Documents can be listed, opened, disabled, or deleted.
- Document versions are tracked when a file is replaced.

### Ingestion pipeline

- Uploaded documents enter a processing queue.
- Text is extracted from the source file.
- Extracted text is split into chunks.
- Chunks keep metadata: document, page, section, position, version, and visibility scope.
- Embeddings are generated and stored.
- Ingestion status is visible to the user.

### Retrieval

- The system retrieves candidate chunks using vector similarity.
- It supports keyword or hybrid fallback when vector results are weak.
- Results are filtered by workspace and document permissions.
- Retrieved chunks are ranked before answer generation.

### Answer generation

- The user asks a question inside a workspace.
- The backend retrieves relevant context.
- The LLM receives the question and retrieved sources.
- The response includes a direct answer and citations.
- If context is insufficient, the assistant must say that it does not have enough information.

### Evaluation

- Admin users can define a golden set of questions.
- Each question includes expected answer notes and expected source documents.
- The system can run these questions against the current index.
- Results are stored for comparison after changes.

### Dashboard

- Show document count, processed count, failed count, and recent ingestion logs.
- Show recent questions and citation usage.
- Show evaluation score summary.

## 6. Non-functional requirements

### Security

- All retrieval queries must be scoped by workspace.
- The system must simulate document-level access restrictions in the MVP.
- API endpoints must validate authorization.
- Secrets must be stored in environment variables.
- Uploaded files must not be publicly accessible by default.

### Reliability

- Failed ingestion jobs must be visible and retryable.
- The answer endpoint must handle missing context gracefully.
- The system must not fabricate citations.

### Performance

- The MVP should handle small document collections comfortably.
- Target demo scale: 20 to 100 documents, 5,000 to 50,000 chunks depending on chunk size.
- Retrieval latency should be acceptable for a portfolio demo.

### Maintainability

- Code must be organized by domain modules.
- Database migrations must be versioned.
- Prompt templates must be stored separately from business logic.
- Provider integrations must use abstractions.

### Observability

- The backend must expose a healthcheck endpoint.
- Logs must include request ID, workspace ID, operation, duration, and error details.
- Ingestion steps must produce structured status records.

## 7. Main modules

1. Authentication and authorization.
2. Workspace and user management.
3. Document upload and metadata.
4. Ingestion pipeline.
5. Chunking and embedding.
6. Retrieval and ranking.
7. Answer generation.
8. Citation builder.
9. Evaluation workflow.
10. Dashboard and reporting.
11. Observability and operational tooling.

## 8. Technical view

The system should use a web frontend, an API backend, PostgreSQL with pgvector, a file storage layer, an embedding provider, and a chat model provider.

The backend owns the security boundary. The frontend never calls the LLM provider directly.

## 9. Portfolio value

This project is valuable because it combines several marketable skills in one product:

- TypeScript frontend;
- Python backend;
- SQL and data modeling;
- vector search;
- RAG design;
- document processing;
- security-aware AI;
- evaluation and testing;
- deployment and documentation.

## 10. Success criteria

The MVP is successful when a reviewer can:

1. open a live demo;
2. upload or use sample documents;
3. ask questions;
4. receive grounded answers with citations;
5. inspect architecture and local setup;
6. run the project locally from documentation;
7. see tests and evaluation evidence.
