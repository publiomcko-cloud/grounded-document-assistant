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

Then run the frontend and backend according to the commands defined in `docs/local_setup_execution.md`.

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

Planning/documentation phase. This package defines the implementation direction before coding begins.

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
