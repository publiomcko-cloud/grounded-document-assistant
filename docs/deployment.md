# Deployment - Grounded Document Assistant

This document describes the public portfolio deployment path for Grounded Document Assistant.

Target stack:

- Frontend: Vercel
- Backend API: Render web service
- Database: Supabase PostgreSQL with `pgvector`
- Redis queue/health dependency: Render Key Value
- Ingestion mode for first public demo: inline ingestion with `INGESTION_QUEUE_EAGER=true`

The repository now includes:

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `render.yaml`

## 1. Current Deployment Status

- Frontend: pending deployment
- Backend health: pending deployment
- API docs: pending deployment
- Demo video: pending recording

The first public demo should use only synthetic demo data and demo credentials.

## 2. Important Architecture Decision

The current app stores uploaded files on local disk through `FILE_STORAGE_PATH`.

On one local machine, that works with a separate backend and worker because both processes can read the same files. On Render, a web service and a worker service do not automatically share the same filesystem.

For the first online portfolio demo, use:

```env
INGESTION_QUEUE_EAGER=true
FILE_STORAGE_PATH=/tmp/grounded-document-assistant-storage
```

That makes uploads process inline inside the backend web service. It avoids a paid always-on worker and avoids cross-service file-sharing problems.

Use a separate Render worker only after adding shared object storage, such as Supabase Storage or S3-compatible storage.

## 3. Supabase Setup

You must do this outside the repository in the Supabase dashboard.

1. Open Supabase.
2. Create a new project.
3. Open the SQL editor.
4. Run:

```sql
create extension if not exists vector;
```

5. Open project database settings.
6. Copy the PostgreSQL connection string.
7. Convert the URL scheme for SQLAlchemy/psycopg:

```text
postgresql://...        -> postgresql+psycopg://...
```

8. Keep the final value private. It will be used as Render's `DATABASE_URL`.

Recommended format:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require
```

## 4. Render Setup

Render is used for the backend API and Redis-compatible Key Value service.

### Step 1 - Push the repository

Push the current branch to GitHub before creating the Render Blueprint.

### Step 2 - Create the Blueprint

In Render:

1. Choose `New`.
2. Choose `Blueprint`.
3. Select the GitHub repository.
4. Render should detect `render.yaml`.
5. Create the services.

The Blueprint creates:

- `grounded-document-assistant-api`
- `grounded-document-assistant-redis`

### Step 3 - Fill Render environment variables

Render will prompt for variables marked `sync: false`.

Set:

```env
DATABASE_URL=postgresql+psycopg://...supabase...?sslmode=require
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
LLM_API_KEY=
LLM_BASE_URL=
EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=
```

Render injects `REDIS_HOST` and `REDIS_PORT` automatically from the Key Value service defined in `render.yaml`.

For the first deploy, `CORS_ORIGINS` can use local origins. After Vercel gives you a frontend URL, update it to:

```env
CORS_ORIGINS=https://YOUR-VERCEL-APP.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

### Step 4 - Verify backend deploy

Render runs:

```bash
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

After deploy, open:

```text
https://YOUR-RENDER-SERVICE.onrender.com/health
https://YOUR-RENDER-SERVICE.onrender.com/docs
```

Expected `/health` response:

```json
{
  "status": "ok",
  "environment": "production",
  "checks": {
    "database": {"status": "ok"},
    "redis": {"status": "ok"}
  }
}
```

## 5. Vercel Setup

You must do this outside the repository in the Vercel dashboard.

1. Open Vercel.
2. Import the GitHub repository.
3. Set the project root directory to:

```text
frontend
```

4. Set the environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

5. Deploy the frontend.
6. Copy the Vercel frontend URL.
7. Return to Render and update `CORS_ORIGINS` to include the Vercel URL.
8. Redeploy or restart the Render backend.

## 6. Public Demo Validation

After Render and Vercel are deployed, validate in this order.

### Backend health

```bash
curl https://YOUR-RENDER-SERVICE.onrender.com/health
```

Expected:

```text
"status":"ok"
```

### API docs

Open:

```text
https://YOUR-RENDER-SERVICE.onrender.com/docs
```

Expected:

- FastAPI docs load.
- Auth, documents, retrieval, chat, evaluations, and dashboard routes are visible.

### Frontend

Open:

```text
https://YOUR-VERCEL-APP.vercel.app
```

Expected:

- landing page loads;
- login page loads;
- owner demo-fill button works.

### Login

Use:

```text
owner@example.com
grounded-demo
```

Expected:

- dashboard loads;
- health diagnostics show PostgreSQL and Redis as healthy.

### Document upload

Upload a small `.txt` document.

Expected:

- upload succeeds;
- because `INGESTION_QUEUE_EAGER=true`, processing runs inline;
- document becomes processed;
- chunks and embeddings appear.

### Chat

Ask a question about the uploaded or seeded document.

Expected:

- assistant returns a grounded answer;
- citations are attached;
- citations refer to allowed documents only.

### Evaluation

Open `/app/evaluations`.

Expected:

- seeded evaluation set appears;
- custom evaluation set creation works;
- evaluation run completes.

## 7. Optional Worker Upgrade

Do this only after shared file storage exists.

Required before enabling a separate worker:

- implement Supabase Storage or S3-compatible storage adapter;
- ensure backend uploads are readable by the worker;
- set `INGESTION_QUEUE_EAGER=false`;
- add or uncomment the `type: worker` service in `render.yaml`;
- use a paid Render worker plan if required;
- redeploy backend and worker.

Worker command:

```bash
python -m app.workers.run
```

## 8. Required Environment Variables

Backend on Render:

```env
DATABASE_URL=postgresql+psycopg://...supabase...?sslmode=require
REDIS_HOST=<injected-from-render-key-value>
REDIS_PORT=<injected-from-render-key-value>
APP_ENV=production
JWT_SECRET=<generated-by-render>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=https://YOUR-VERCEL-APP.vercel.app,http://localhost:3000,http://127.0.0.1:3000
FILE_STORAGE_PATH=/tmp/grounded-document-assistant-storage
MAX_UPLOAD_MB=25
INGESTION_CHUNK_SIZE_WORDS=180
INGESTION_CHUNK_OVERLAP_WORDS=30
INGESTION_QUEUE_NAME=grounded-document-assistant-ingestion
INGESTION_JOB_TIMEOUT_SECONDS=600
INGESTION_QUEUE_EAGER=true
LLM_PROVIDER=local
LLM_API_KEY=
LLM_BASE_URL=
CHAT_MODEL=local-grounded-answerer
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=local-hash-1536
EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=
EMBEDDING_REQUEST_TIMEOUT_SECONDS=30
RETRIEVAL_TOP_K_DEFAULT=5
ANSWER_MAX_CITATIONS=3
```

Frontend on Vercel:

```env
NEXT_PUBLIC_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

Future production variables:

```env
FILE_STORAGE_PROVIDER=supabase-storage-or-s3
FILE_STORAGE_BUCKET=
FILE_STORAGE_ACCESS_KEY=
FILE_STORAGE_SECRET_KEY=
```

These future storage variables are not implemented yet.

## 9. Demo Safety

- Use only synthetic demo documents.
- Do not upload real customer, legal, medical, financial, or private company documents.
- Use demo credentials only.
- Keep all real database passwords, Redis connection details, JWT secrets, and provider API keys in platform environment variables.
- Do not commit `.env`.

## 10. Post-Deployment Checklist

- [ ] Supabase project created.
- [ ] `vector` extension enabled.
- [ ] Render Blueprint created.
- [ ] Render backend deployed.
- [ ] Render Key Value created.
- [ ] `DATABASE_URL` configured in Render.
- [ ] `REDIS_HOST` and `REDIS_PORT` injected from Render Key Value.
- [ ] Render `/health` returns `ok`.
- [ ] Render `/docs` loads.
- [ ] Vercel frontend deployed.
- [ ] `NEXT_PUBLIC_API_BASE_URL` configured in Vercel.
- [ ] Render `CORS_ORIGINS` includes the Vercel URL.
- [ ] Owner demo login works.
- [ ] Upload and inline ingestion work.
- [ ] Chat returns citations.
- [ ] Evaluation run completes.
- [ ] README live demo links updated.
- [ ] Screenshots captured.
- [ ] Demo video recorded.

## 11. References

- Render Blueprint specification: https://render.com/docs/blueprint-spec
- Render Key Value: https://render.com/docs/key-value
- Supabase pgvector guide: https://supabase.com/docs/guides/database/extensions/pgvector
- Vercel environment variables: https://vercel.com/docs/environment-variables
