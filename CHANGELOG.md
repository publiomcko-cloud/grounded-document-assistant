# Changelog

All notable changes to Grounded Document Assistant will be documented in this file.

## [Unreleased]

### Changed

- Started the portfolio-readiness cleanup based on the DataPulse Commerce standard.
- Moved historical planning documents into `docs/archive/`.
- Replaced the default frontend README with project-specific frontend documentation.
- Reworked the root README into a recruiter/client-facing portfolio entry point.

## [0.1.0] - 2026-06-30

### Added

- FastAPI backend with SQLAlchemy, Alembic, PostgreSQL, and `pgvector`.
- Next.js frontend with dashboard, document management, chat, and evaluation screens.
- JWT authentication, seeded owner/viewer users, and workspace membership checks.
- Document upload for text and text-based PDF files.
- Redis/RQ ingestion worker with extraction, chunking, embeddings, and ingestion logs.
- Permission-aware retrieval with vector search and PostgreSQL keyword fallback.
- Grounded chat answers with persisted messages and validated citations.
- Evaluation sets, custom evaluation creation, evaluation runs, and score summaries.
- Local deterministic answer and embedding providers for free local demos.
- Backend test suite, frontend validation scripts, GitHub Actions CI, and live smoke script.
- MIT license.

### Known Limitations

- Public deployment is still pending.
- Demo screenshots and demo video are still pending.
- Local answer and embedding providers are deterministic development providers, not production model quality.
- File storage currently uses local disk by default.
- Browser E2E tests are not implemented yet.
