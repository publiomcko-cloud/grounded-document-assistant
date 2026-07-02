# Deployment - Grounded Document Assistant

This guide is a click-by-click runbook for deploying Grounded Document Assistant as a public portfolio demo.

Target stack:

- Frontend: Vercel
- Backend API: Render web service
- Database: Supabase PostgreSQL with `pgvector`
- Redis-compatible dependency: Render Key Value
- First demo ingestion mode: inline ingestion with `INGESTION_QUEUE_EAGER=true`

Current public demo URLs:

```text
Frontend: https://grounded-document-assistant.vercel.app
Backend:  https://grounded-document-assistant-api.onrender.com
Health:   https://grounded-document-assistant-api.onrender.com/health
Docs:     https://grounded-document-assistant-api.onrender.com/docs
```

Repository deployment files:

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/vercel.json`
- `render.yaml`

Important deployment lessons from this project:

- Render free services do not support `preDeployCommand`.
- Render Shell is not available on the free plan.
- Vercel must deploy the `frontend` directory, not the repository root.
- Vercel must use the Next.js framework builder. The committed `frontend/vercel.json` forces this.
- Vercel Deployment Protection or SSO protection must be disabled for a public portfolio demo.
- `NEXT_PUBLIC_API_BASE_URL` must not be blank, and Vercel must be redeployed after changing it.
- Render `CORS_ORIGINS` must include the exact Vercel origin or browser login will fail.

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

At first deploy time, the Vercel URL may not exist yet. After the Vercel deployment is created, update `CORS_ORIGINS` to include the live frontend URL:

```env
CORS_ORIGINS=https://grounded-document-assistant.vercel.app,http://localhost:3000,http://127.0.0.1:3000
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

Render Shell is not available on the free plan, so the free-tier path is to run migrations and seed from your local terminal against the Supabase database.

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

Optional paid-plan convenience:

If your Render plan includes Shell, you can open `grounded-document-assistant-api`, click `Shell`, and run:

```bash
alembic upgrade head
python -m app.db.seed
```

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

The repository also includes `frontend/vercel.json` with `framework: "nextjs"` so Vercel keeps the project on the Next.js deployment builder even if the dashboard initially shows `Other`.

If the dashboard still shows `Framework Preset: Other`, continue only after confirming `frontend/vercel.json` is committed and pushed. A deployment can say `Ready` but still return Vercel `404: NOT_FOUND` if Vercel builds without the Next.js deployment builder.

Expected:

```text
Install Command: npm install or npm ci
Build Command: npm run build
Output Directory: Next.js default
```

Do not set the output directory to `public`, `.`, `out`, or `.next`. Leave it as the Next.js default.

### Step 3 - Disable Deployment Protection For Public Demo

Vercel may protect generated deployment URLs with SSO or Deployment Protection. That is useful for private previews, but it blocks a public portfolio demo.

In Vercel:

1. Open the `grounded-document-assistant` project.
2. Click `Settings`.
3. Look for `Deployment Protection`, `Security`, or `Vercel Authentication`.
4. Disable SSO or deployment protection for the public demo.
5. Save the setting.

If using the Vercel CLI, this command disables SSO protection for this project:

```bash
npx vercel project protection disable grounded-document-assistant --sso --scope publio1
```

### Step 4 - Add Environment Variable

In the Vercel import screen, find `Environment Variables`.

Add:

```env
NEXT_PUBLIC_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

Use the exact Render backend URL from the previous section.

For this project, the current value is:

```env
NEXT_PUBLIC_API_BASE_URL=https://grounded-document-assistant-api.onrender.com
```

Important:

- The value must not be empty.
- Select the `Production` environment.
- If you edit this variable after deployment, redeploy Vercel because `NEXT_PUBLIC_*` values are baked into the browser bundle.

### Step 5 - Deploy

1. Click `Deploy`.
2. Wait for the build to finish.
3. Open the deployed Vercel URL.

It will look like:

```text
https://grounded-document-assistant.vercel.app
```

Copy this URL.

Expected successful Vercel build signs:

```text
Detected Next.js version
Running "npm run build"
Running onBuildComplete from Vercel
Route (app)
- /
- /app
- /login
- /register
```

If the deployment logs only show `Builds . [0ms]` in `vercel inspect`, the deployment is not using the proper Next.js builder. Confirm `frontend/vercel.json` is committed, redeploy, and do not override the output directory.

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

For the current public demo, the correct value is:

```env
CORS_ORIGINS=https://grounded-document-assistant.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

After Render redeploys, test CORS from your local terminal:

```bash
curl -i -X OPTIONS 'https://grounded-document-assistant-api.onrender.com/auth/login' \
  -H 'Origin: https://grounded-document-assistant.vercel.app' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type'
```

Expected:

```text
HTTP/2 200
access-control-allow-origin: https://grounded-document-assistant.vercel.app
```

If the response says `Disallowed CORS origin`, Render has not received or redeployed the correct `CORS_ORIGINS` value yet.

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

Terminal check:

```bash
curl -I https://grounded-document-assistant.vercel.app/
curl -I https://grounded-document-assistant.vercel.app/login
```

Expected:

```text
HTTP/2 200
```

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

## 8. Verify README After Deployment

After validation passes, confirm `README.md` contains the public demo links.

Current expected values:

```md
- Frontend: https://grounded-document-assistant.vercel.app
- Backend health: https://grounded-document-assistant-api.onrender.com/health
- API docs: https://grounded-document-assistant-api.onrender.com/docs
- Demo video: docs/demo_video/grounded-document-assistant-demo.mp4
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
- [ ] `frontend/vercel.json` is committed and pushed.
- [ ] Vercel Framework Preset is `Next.js` or the committed `vercel.json` forces Next.js.
- [ ] Vercel Deployment Protection or SSO protection is disabled for the public demo.
- [ ] `NEXT_PUBLIC_API_BASE_URL` configured in Vercel.
- [ ] Vercel redeployed after setting `NEXT_PUBLIC_API_BASE_URL`.
- [ ] Render `CORS_ORIGINS` includes the Vercel URL.
- [ ] Render redeployed after setting `CORS_ORIGINS`.
- [ ] CORS preflight from the Vercel origin succeeds.
- [ ] Owner demo login works.
- [ ] Upload and inline ingestion work.
- [ ] Chat returns citations.
- [ ] Evaluation run completes.
- [ ] README live demo links updated.
- [ ] Screenshots captured.
- [x] Demo video recorded.

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
- `NEXT_PUBLIC_API_BASE_URL` is not empty;
- Render backend is awake;
- Render `CORS_ORIGINS` includes the Vercel frontend URL;
- Vercel was redeployed after changing environment variables.
- Render was redeployed after changing `CORS_ORIGINS`.

For this project, the public demo values should be:

```env
NEXT_PUBLIC_API_BASE_URL=https://grounded-document-assistant-api.onrender.com
CORS_ORIGINS=https://grounded-document-assistant.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

### Vercel shows `404: NOT_FOUND`

This means Vercel is not serving a successful deployment at that URL. It is not a backend or CORS problem.

If Vercel says `Ready` and `grounded-document-assistant.vercel.app` appears under `Domains`, still run the checks below. A deployment can be ready while the production domain is attached to the wrong deployment, the wrong branch, or a project that was imported from the repository root instead of `frontend`.

In this project, the most common cause was Vercel treating the app as `Other` instead of `Next.js`. Keep `frontend/vercel.json` committed:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "nextjs"
}
```

First check whether the deployment itself works:

1. Open `https://vercel.com/dashboard`.
2. Open the `grounded-document-assistant` project.
3. Click `Deployments`.
4. Click the latest deployment that says `Ready`.
5. Click `Visit` from that deployment page.

If the unique deployment URL also shows `404: NOT_FOUND`, Vercel probably deployed the repository root instead of the frontend app.

Fix the project root:

1. Open the Vercel project.
2. Click `Settings`.
3. Click `General`.
4. Find `Root Directory`.
5. Confirm it is exactly:

```text
frontend
```

6. If the root directory was wrong, change it to `frontend`.
7. Click `Save`.
8. Go back to `Deployments`.
9. Click the three dots on the latest deployment.
10. Click `Redeploy`.
11. Do not reuse the build cache if Vercel offers that option.
12. After the deployment is ready, click `Visit`.

If the unique deployment URL works but `https://grounded-document-assistant.vercel.app` still shows `404: NOT_FOUND`, the domain is assigned incorrectly or is not pointing at the production deployment.

Check the project domain:

1. Open the Vercel project.
2. Click `Settings`.
3. Click `Domains`.
4. Confirm `grounded-document-assistant.vercel.app` is listed.
5. Confirm it is assigned to the current project.
6. If the domain exists but still returns 404, remove it and add it again.
7. Go back to `Deployments`.
8. Open the latest `Ready` production deployment.
9. Click the deployment actions menu.
10. Click `Promote to Production` if that option appears.

Also confirm the production branch:

1. Open the Vercel project.
2. Click `Settings`.
3. Click `Git`.
4. Confirm `Production Branch` matches the branch you pushed, usually:

```text
main
```

Finally, confirm the domain is not attached to another Vercel project:

1. Open the Vercel project.
2. Click `Settings`.
3. Click `Domains`.
4. Click `grounded-document-assistant.vercel.app`.
5. Confirm the domain belongs to this project and points to the latest production deployment.

If using the Vercel CLI, inspect the production deployment:

```bash
npx vercel inspect https://grounded-document-assistant.vercel.app --scope publio1
```

Healthy output should show Next.js output items under `Builds`, not only:

```text
Builds
  . [0ms]
```

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
