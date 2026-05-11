# Deployment Strategy — Grounded Document Assistant

## 1. Deployment objective

Deploy a public demo that is stable enough for portfolio review and realistic enough to show business value.

The deployment must support:

- frontend access;
- backend API;
- PostgreSQL with pgvector;
- private file storage;
- environment variables;
- healthcheck;
- demo data.

## 2. Recommended deployment architecture

```text
User
  -> Frontend hosting
    -> Backend API hosting
      -> Managed PostgreSQL with pgvector
      -> Redis or background worker service
      -> Private file storage
      -> LLM/Embedding provider
```

## 3. Suggested services

### Frontend

Options:

- Vercel;
- Netlify;
- Cloudflare Pages.

### Backend

Options:

- Render;
- Railway;
- Fly.io;
- VPS with Docker;
- cloud container service.

### Database

Options:

- managed PostgreSQL with pgvector support;
- self-hosted PostgreSQL with pgvector on VPS;
- Supabase if it fits implementation needs.

### File storage

Options:

- S3-compatible object storage;
- local storage only for private demo VPS;
- Supabase Storage if already using Supabase.

## 4. Environment variables

Minimum production variables:

```text
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
FILE_STORAGE_PROVIDER=
FILE_STORAGE_BUCKET=
FILE_STORAGE_ACCESS_KEY=
FILE_STORAGE_SECRET_KEY=
LLM_PROVIDER=
LLM_API_KEY=
LLM_BASE_URL=
CHAT_MODEL=
EMBEDDING_MODEL=
MAX_UPLOAD_MB=
APP_ENV=production
```

## 5. Publication order

1. Create production database.
2. Enable pgvector extension.
3. Configure backend environment variables.
4. Deploy backend.
5. Run migrations.
6. Seed demo data.
7. Configure frontend environment variables.
8. Deploy frontend.
9. Test login.
10. Test document retrieval and citations.
11. Run golden set evaluation.
12. Update README with live demo link.

## 6. Healthcheck

Backend must expose:

```text
GET /health
```

Expected response:

```json
{"status":"ok"}
```

Optional expanded response:

```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "version": "1.0.0"
}
```

## 7. Logs

Production logs should include:

- request ID;
- endpoint;
- workspace ID when available;
- user ID when available;
- operation duration;
- ingestion step;
- retrieval count;
- model name;
- error details without leaking secrets.

## 8. Post-deployment validation

After deployment, validate:

- frontend loads;
- backend healthcheck works;
- login works;
- sample documents are processed;
- chat returns citations;
- restricted document test passes;
- evaluation run completes;
- README demo instructions match the deployed system.

## 9. Demo data strategy

Use safe public or synthetic documents. Do not upload private real-world documents to the public demo.

Recommended sample documents:

- synthetic company FAQ;
- synthetic refund policy;
- synthetic onboarding guide;
- synthetic restricted internal procedure.

## 10. Deployment risks

| Risk | Mitigation |
|---|---|
| pgvector unavailable | Choose provider with extension support or deploy PostgreSQL manually. |
| File storage exposed publicly | Use signed URLs or backend-controlled file access. |
| Secrets leaked | Use platform environment variables and never commit `.env`. |
| Demo breaks after inactivity | Choose hosting with predictable sleep behavior or document cold starts. |
| Model costs grow | Use small demo documents, rate limits, and token logging. |

## 11. Final deployment checklist

- [ ] Production database created.
- [ ] pgvector enabled.
- [ ] Backend deployed.
- [ ] Frontend deployed.
- [ ] Environment variables configured.
- [ ] Migrations applied.
- [ ] Demo seed loaded.
- [ ] Healthcheck passing.
- [ ] Public demo tested.
- [ ] Evaluation run tested.
- [ ] README updated with live links.
