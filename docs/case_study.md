# Case Study - Grounded Document Assistant

## Problem

Small teams often keep important information scattered across PDFs, manuals, internal policies, onboarding documents, product guides, and support notes. When someone needs an answer, they have to search manually, ask another person, or trust memory.

That creates slow support workflows, inconsistent answers, repeated questions, and a higher risk of using outdated or incomplete information.

For AI systems, the problem is sharper: a generic chatbot can sound confident while inventing facts. A useful document assistant needs to ground answers in retrieved sources, show citations, and respect access boundaries.

## Target Users

Grounded Document Assistant is designed for:

- small and medium businesses with document-heavy operations;
- support teams that answer repeated questions from internal policies or product materials;
- founders or operators who need a searchable internal knowledge base;
- teams evaluating AI assistants for manuals, FAQs, onboarding, or procedures;
- recruiters and technical reviewers assessing full-stack applied AI skills.

## Solution

The project implements a full-stack document assistant that lets users upload documents, process them into searchable chunks, ask natural-language questions, and receive answers with citations.

The app includes the surrounding product system needed to make the AI flow credible:

- authentication;
- workspace scoping;
- document visibility rules;
- background ingestion;
- vector and keyword retrieval;
- grounded answers;
- persisted citations;
- evaluation sets and runs;
- operational dashboard.

This makes the project more than a chatbot demo. It shows the workflow around AI: data ingestion, access control, retrieval quality, observability, and repeatable evaluation.

## Main Features

- Owner and viewer demo accounts.
- Workspace-aware protected app shell.
- Document upload for text and text-based PDFs.
- Private local file storage.
- Asynchronous ingestion worker with Redis and RQ.
- Text extraction, chunking, embeddings, and ingestion logs.
- PostgreSQL storage with `pgvector`.
- Permission-aware vector search and keyword fallback.
- Chat answers with citations linked to stored chunks.
- Conversation history and conversation deletion.
- Document content preview and chunk preview.
- Seeded golden evaluation set.
- Custom evaluation set creation.
- Evaluation runs with scores and retrieved-source tracking.
- Dashboard with document status, ingestion activity, recent questions, evaluation snapshot, and service health.
- Local smoke script and automated backend/frontend validation.

## Architecture

```text
Browser
  -> Next.js frontend
  -> FastAPI backend
  -> PostgreSQL with pgvector
  -> Redis queue
  -> RQ ingestion worker
  -> local or OpenAI-compatible AI providers
  -> private file storage
```

The frontend is responsible for user workflows: login, dashboard, documents, chat, and evaluations.

The backend is the control layer. It validates identity, applies workspace and role rules, manages document metadata, orchestrates ingestion jobs, performs retrieval, generates answers, validates citations, and persists evaluation results.

The worker handles long-running document processing outside the request cycle. That keeps upload requests responsive while extraction, chunking, and embeddings happen asynchronously.

## AI/RAG Flow

1. A user uploads a document.
2. The backend validates the file and stores it privately.
3. The backend creates document and document-version records.
4. The backend enqueues an ingestion job.
5. The worker extracts text from the file.
6. The worker splits text into overlapping chunks.
7. The embedding provider creates vectors for each chunk.
8. Chunks and embeddings are stored in PostgreSQL with `pgvector`.
9. A user asks a question in chat.
10. The backend retrieves relevant chunks scoped by workspace and document permissions.
11. Keyword fallback can supplement vector retrieval.
12. The answer provider generates a grounded answer from retrieved context.
13. The backend validates that citations refer to retrieved chunks.
14. The assistant message and citations are persisted.
15. The frontend displays the answer and source references.

## Technical Decisions

### FastAPI Backend

FastAPI fits the backend because the system has API-heavy workflows, typed request/response schemas, background worker coordination, and a natural boundary between frontend and AI/document services.

### PostgreSQL and pgvector

PostgreSQL keeps relational data, permissions, conversations, citations, and evaluation history in one consistent system. `pgvector` allows embeddings to live near the document and workspace metadata needed for secure filtering.

### Redis Worker

Document processing can be slow. A Redis/RQ worker keeps uploads responsive and makes ingestion status visible through logs and document statuses.

### Local Providers by Default

The default answer and embedding providers are deterministic local providers. This keeps the portfolio demo inexpensive, predictable, and usable without external API keys.

The code also includes OpenAI-compatible provider configuration paths so the architecture can move toward real hosted models later.

### Permission-Aware Retrieval

The backend enforces workspace and visibility filters during retrieval. This is important because AI systems can leak information if retrieval is treated as only a relevance problem.

### Evaluation Workflow

The evaluation module demonstrates quality awareness. Golden questions, expected notes, retrieved chunks, generated answers, and scores make it possible to test changes to ingestion, retrieval, and prompting over time.

## Trade-offs

- The local AI providers are useful for deterministic demos but do not represent production model quality.
- File storage currently uses local disk, which is simple for local development but not enough for durable public uploads.
- PDF parsing focuses on text-based PDFs; OCR for scanned documents is future work.
- Workspace and visibility rules demonstrate access-boundary thinking but are not a full enterprise authorization model.
- Browser E2E tests are still pending.
- Public deployment is planned but not yet complete.

## Results

The current local MVP proves the core product loop:

- documents can be uploaded and processed;
- chunks and embeddings are persisted;
- retrieval is workspace-aware and permission-aware;
- chat answers include validated citations;
- conversations and citations are stored;
- evaluation runs can be created and reviewed;
- the dashboard exposes operational status;
- automated tests and smoke checks validate critical behavior.

The project is ready for final portfolio packaging and public deployment work.

## Next Steps

- Add Render/Vercel/Supabase deployment assets.
- Choose and configure a public Redis provider.
- Decide whether public uploads need persistent object storage.
- Create `docs/demo_script.md`.
- Create `docs/portfolio_readiness.md`.
- Capture screenshots after public demo data is stable.
- Record a short demo video.
- Add Playwright browser E2E coverage.
- Replace pending README demo links with deployed URLs.
- Add optional Supabase Storage or S3-compatible file storage for persistent public uploads.
