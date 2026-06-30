# Deployment - Grounded Document Assistant

This guide is a click-by-click runbook for deploying Grounded Document Assistant as a public portfolio demo.

Target stack:

- Frontend: Vercel
- Backend API: Render web service
- Database: Supabase PostgreSQL with `pgvector`
- Redis-compatible dependency: Render Key Value
- First demo ingestion mode: inline ingestion with `INGESTION_QUEUE_EAGER=true`

Repository deployment files:

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `render.yaml`

## 1. Before You Start

You need accounts for:

- GitHub
- Supabase
- Render
- Vercel

You also need the latest local changes pushed to GitHub. The deployment platforms read from GitHub, not from your local machine.

From the project root, check your current changes:

```bash
git status
```

After reviewing changes, commit and push them:

```bash
git add .
git commit -m "Add portfolio deployment assets"
git push origin main
```

If you are not working on `main`, push your current branch and select that branch inside Render/Vercel.

## 2. Deployment Shape

For the first online demo, the backend processes uploaded documents inline:

```env
INGESTION_QUEUE_EAGER=true
FILE_STORAGE_PATH=/tmp/grounded-document-assistant-storage
```

Why:

- local file storage is not shared between separate Render services;
- a separate Render worker may require a paid plan;
- inline ingestion keeps the first portfolio demo simpler and functional.

Later, after adding Supabase Storage or S3-compatible storage, you can enable a separate background worker.

## 3. Supabase Database

Use Supabase for PostgreSQL and `pgvector`.

### Step 1 - Create The Project

1. Go to `https://supabase.com`.
2. Sign in.
3. Click `New project`.
4. Choose your organization.
5. Fill:
   - `Project name`: `grounded-document-assistant`
   - `Database Password`: generate and store a strong password
   - `Region`: choose the closest region to your expected users
6. Click `Create new project`.
7. Wait until the project is ready.

### Step 2 - Enable pgvector

1. In the Supabase project sidebar, click `SQL Editor`.
2. Click `New query`.
3. Paste:

```sql
create extension if not exists vector;
```

4. Click `Run`.
5. Confirm the query succeeds.

### Step 3 - Copy The Database URL

1. In the Supabase project sidebar, click `Project Settings`.
2. Click `Database`.
3. Find `Connection string`.
4. Choose a connection string format compatible with normal PostgreSQL clients.
5. Copy the URI.
6. Convert the beginning from:

```text
postgresql://
```

to:

```text
postgresql+psycopg://
```

7. Add `?sslmode=require` if it is not already present.

Final shape:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require
```

Keep this value private. You will paste it into Render as `DATABASE_URL`.

## 4. Render Backend

Use Render for the FastAPI backend and Render Key Value service.

### Step 1 - Create A Blueprint

1. Go to `https://dashboard.render.com`.
2. Sign in.
3. Click `New +`.
4. Click `Blueprint`.
5. Connect GitHub if Render asks.
6. Select the repository:

```text
publiomcko-cloud/grounded-document-assistant
```

7. Select the branch you pushed.
8. Render should detect:

```text
render.yaml
```

9. Click `Apply` or `Create Blueprint`.

Render should create:

- `grounded-document-assistant-api`
- `grounded-document-assistant-redis`

### Step 2 - Fill Required Values

During Blueprint setup, Render will ask for variables marked `sync: false`.

Fill:

```env
DATABASE_URL=postgresql+psycopg://...supabase...?sslmode=require
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Do not fill `REDIS_HOST` or `REDIS_PORT` manually. Render injects those from `grounded-document-assistant-redis`.

Render generates `JWT_SECRET` automatically.

### Step 3 - Wait For Deploy

1. Open the `grounded-document-assistant-api` service.
2. Click the `Events` or `Logs` tab.
3. Watch the deploy.

Render should run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The free Render tier does not support `preDeployCommand`, so migrations and seed data are run manually in the next step.

### Step 4 - Run Migrations And Seed Data

You must run this after the Render service has environment variables configured.

Preferred option if Render Shell is available:

1. Open `grounded-document-assistant-api` in Render.
2. Click `Shell`.
3. Run:

```bash
alembic upgrade head
python -m app.db.seed
```

Fallback option from your local terminal:

1. Open a terminal in the project root.
2. Activate the backend virtual environment:

```bash
source backend/.venv/bin/activate
```

3. Export the same Supabase URL you used in Render:

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require'
```

4. Run migrations:

```bash
cd backend
alembic upgrade head
```

5. Run seed data:

```bash
python -m app.db.seed
```

6. Return to the project root:

```bash
cd ..
```

Important: run the seed only against the dedicated Supabase demo database, never against a database containing real private documents or customer data.

### Step 5 - Copy The Backend URL

1. Open the `grounded-document-assistant-api` service.
2. Find the public service URL near the top of the service page.
3. It will look like:

```text
https://grounded-document-assistant-api.onrender.com
```

Save this URL. You need it for Vercel.

### Step 6 - Verify Backend Health

Open these URLs in your browser:

```text
https://YOUR-RENDER-SERVICE.onrender.com/health
https://YOUR-RENDER-SERVICE.onrender.com/docs
```

Expected `/health` shape:

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

If `/health` is `degraded`, check:

- `DATABASE_URL` is correct;
- Supabase database is active;
- `vector` extension is enabled;
- migrations were run successfully;
- seed data was created successfully;
- Render Key Value service exists;
- `REDIS_HOST` and `REDIS_PORT` are present in the backend environment.

## 5. Vercel Frontend

Use Vercel for the Next.js frontend.

### Step 1 - Import The Repository

1. Go to `https://vercel.com/dashboard`.
2. Sign in.
3. Click `Add New`.
4. Click `Project`.
5. Import:

```text
publiomcko-cloud/grounded-document-assistant
```

### Step 2 - Configure Project Settings

In the import screen:

1. Set `Framework Preset` to `Next.js`.
2. Set `Root Directory` to:

```text
frontend
```

3. Leave install/build commands as Vercel defaults unless Vercel asks.

Expected:

```text
Install Command: npm install or npm ci
Build Command: npm run build
Output Directory: Next.js default
```

### Step 3 - Add Environment Variable

In the Vercel import screen, find `Environment Variables`.

Add:

```env
NEXT_PUBLIC_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

Use the exact Render backend URL from the previous section.

### Step 4 - Deploy

1. Click `Deploy`.
2. Wait for the build to finish.
3. Open the deployed Vercel URL.

It will look like:

```text
https://grounded-document-assistant.vercel.app
```

Copy this URL.

## 6. Update Render CORS

After Vercel gives you the public frontend URL, update Render.

1. Go back to `https://dashboard.render.com`.
2. Open `grounded-document-assistant-api`.
3. Click `Environment`.
4. Find `CORS_ORIGINS`.
5. Replace the value with:

```env
https://YOUR-VERCEL-APP.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

6. Click `Save Changes`.
7. Render should redeploy automatically.
8. If it does not, click `Manual Deploy`.
9. Click `Deploy latest commit`.

## 7. Public Demo Validation

Validate in this exact order.

### Backend Health

Open:

```text
https://YOUR-RENDER-SERVICE.onrender.com/health
```

Expected:

```text
"status":"ok"
```

### API Docs

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
- owner and viewer demo-fill buttons are visible.

### Login

1. Open `/login`.
2. Click `Use owner demo`.
3. Submit the form.

Expected:

- dashboard loads;
- health diagnostics show PostgreSQL and Redis as healthy.

### Document Upload

1. Open `/app/documents`.
2. Upload a small `.txt` document.
3. Use title:

```text
Public Demo Test Document
```

4. Use visibility:

```text
workspace
```

Expected:

- upload succeeds;
- processing happens inline;
- document becomes `processed`;
- chunks and embeddings appear.

### Chat

1. Open `/app/chat`.
2. Ask a question about the uploaded or seeded document.

Expected:

- assistant returns an answer;
- citations are attached;
- citations refer only to allowed workspace documents.

### Evaluation

1. Open `/app/evaluations`.
2. Run the seeded evaluation set.

Expected:

- run completes;
- score summary appears;
- result rows appear.

## 8. Update README After Deployment

After validation passes, update `README.md`.

Replace:

```md
- Frontend: pending deployment
- Backend health: pending deployment
- API docs: pending deployment
- Demo video: pending recording
```

with:

```md
- Frontend: https://YOUR-VERCEL-APP.vercel.app
- Backend health: https://YOUR-RENDER-SERVICE.onrender.com/health
- API docs: https://YOUR-RENDER-SERVICE.onrender.com/docs
- Demo video: pending recording
```

## 9. Optional Worker Upgrade

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

## 10. Required Environment Variables

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
CHAT_MODEL=local-grounded-answerer
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=local-hash-1536
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

## 11. Demo Safety

- Use only synthetic demo documents.
- Do not upload real customer, legal, medical, financial, or private company documents.
- Use demo credentials only.
- Keep all real database passwords, Redis connection details, JWT secrets, and provider API keys in platform environment variables.
- Do not commit `.env`.

## 12. Post-Deployment Checklist

- [ ] Repository pushed to GitHub.
- [ ] Supabase project created.
- [ ] `vector` extension enabled.
- [ ] Supabase database URL copied and converted to `postgresql+psycopg://`.
- [ ] Render Blueprint created.
- [ ] Render backend deployed.
- [ ] Render Key Value created.
- [ ] `DATABASE_URL` configured in Render.
- [ ] `REDIS_HOST` and `REDIS_PORT` injected from Render Key Value.
- [ ] Alembic migrations run against Supabase.
- [ ] Demo seed data loaded into Supabase.
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

## 13. Common Issues

### Render health is degraded

Check:

- Supabase URL includes `postgresql+psycopg://`;
- Supabase password is correct;
- Supabase project is not paused;
- `vector` extension was enabled;
- Render Key Value exists;
- `REDIS_HOST` and `REDIS_PORT` exist in Render backend environment variables.

### Browser says failed to fetch

Check:

- `NEXT_PUBLIC_API_BASE_URL` in Vercel points to the Render backend URL;
- Render backend is awake;
- Render `CORS_ORIGINS` includes the Vercel frontend URL;
- Vercel was redeployed after changing environment variables.

### Upload succeeds but document does not process

Check:

- Render backend has `INGESTION_QUEUE_EAGER=true`;
- `FILE_STORAGE_PATH` is set to `/tmp/grounded-document-assistant-storage`;
- Render logs do not show extraction or embedding errors.

### Demo user cannot log in

Check:

- `python -m app.db.seed` was run manually against Supabase;
- Supabase contains the seeded users;
- database migrations completed before seed.

## 14. References

- Render Blueprint specification: https://render.com/docs/blueprint-spec
- Render Key Value: https://render.com/docs/key-value
- Supabase pgvector guide: https://supabase.com/docs/guides/database/extensions/pgvector
- Vercel environment variables: https://vercel.com/docs/environment-variables
