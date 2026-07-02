# Portfolio Readiness - Grounded Document Assistant

This document tracks whether Grounded Document Assistant is ready for public portfolio review by recruiters, technical reviewers, and potential clients.

## Completed

- [x] Public frontend deployed on Vercel.
- [x] FastAPI backend deployed on Render.
- [x] PostgreSQL database hosted on Supabase.
- [x] `pgvector` extension enabled for vector search.
- [x] Render Key Value configured for Redis-compatible health checks and queue support.
- [x] Production migrations applied.
- [x] Demo seed data loaded.
- [x] Vercel `NEXT_PUBLIC_API_BASE_URL` points to the Render backend.
- [x] Render `CORS_ORIGINS` allows the Vercel frontend.
- [x] Frontend returns `200`.
- [x] Backend `/health` returns `ok`.
- [x] API docs open publicly.
- [x] Owner and viewer demo credentials documented.
- [x] Login page includes demo-fill buttons.
- [x] Document upload, ingestion, retrieval, chat, citations, evaluations, and dashboard are implemented.
- [x] Permission-aware retrieval is represented through workspace, restricted, and private document visibility.
- [x] README explains recruiter value, client value, demo flow, architecture, validation, limitations, and safety.
- [x] README includes live frontend, backend health, and API docs links.
- [x] Case study document created.
- [x] Current state document created.
- [x] Deployment guide created and updated with the Vercel/Render fixes discovered during deployment.
- [x] Demo script created.
- [x] Browser screenshots captured for portfolio review.
- [x] README includes screenshots.
- [x] Changelog exists.
- [x] MIT license exists.
- [x] Historical planning docs archived.
- [x] `.env.example` warns against committing secrets and includes required local variables.
- [x] GitHub Actions CI workflow exists.

## Pending

- [ ] Record a 60 to 180 second demo video.
- [ ] Add the demo video link to `README.md`.
- [ ] Add Playwright/browser E2E coverage.
- [ ] Run final backend checks.
- [ ] Run final frontend checks.
- [ ] Run final local smoke test.
- [ ] Run final public demo smoke path in the browser.
- [ ] Confirm owner demo login works after any future deployment changes.
- [ ] Confirm upload, chat citation, and evaluation run work on the public demo after any future deployment changes.

## Review Checklist

- [x] Public frontend link opens.
- [x] Backend `/health` responds.
- [x] API docs open.
- [x] README avoids public links pointing to localhost.
- [x] Demo credentials are documented.
- [x] Known limitations are documented honestly.
- [x] Demo safety guidance is documented.
- [x] Deployment guide explains Supabase, Render, Render Key Value, and Vercel setup.
- [x] Deployment guide documents free-tier Render constraints.
- [x] Deployment guide documents the Vercel Next.js framework fix.
- [x] Deployment guide documents CORS validation.
- [x] Screenshots exist and are valid image files.
- [x] README screenshot references point to existing files.
- [ ] Demo video exists or a hosted video link is available.
- [ ] Browser E2E test can run locally or through a manual workflow.

## Public Demo Links

```text
Frontend: https://grounded-document-assistant.vercel.app
Backend health: https://grounded-document-assistant-api.onrender.com/health
API docs: https://grounded-document-assistant-api.onrender.com/docs
```

## Demo Users

```text
Owner
owner@example.com
grounded-demo

Viewer
viewer@example.com
grounded-demo
```

## Final Classification

Project status: Public-demo deployed and nearly portfolio-ready.

Recommended next action: record the demo video, add the video link to the README, then run final validation.

## Notes

- The first public demo uses inline ingestion on the backend with `INGESTION_QUEUE_EAGER=true`.
- Persistent public uploads are a known limitation until Supabase Storage or S3-compatible storage is added.
- Render free-tier services may cold start after inactivity.
- The deterministic local AI providers keep the demo inexpensive and predictable, but they are not positioned as production model quality.
