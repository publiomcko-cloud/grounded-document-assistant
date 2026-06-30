# Local Setup and Execution Guide — Grounded Document Assistant

## 1. Goal

This guide explains how to create and run the project locally from a clean development environment.

Commands are written assuming WSL Ubuntu.

## 2. Create the project folder

Run inside WSL Ubuntu:

```bash
mkdir -p ~/projects
cd ~/projects
mkdir grounded-document-assistant
cd grounded-document-assistant
```

## 3. Initialize Git

```bash
git init
```

Expected validation:

```bash
git status
```

You should see a clean Git repository on the default branch.

## 4. Add documentation package

Copy the generated documentation files into this repository:

```text
README.md
.env.example
.gitignore
docker-compose.yml
docs/
```

Validate:

```bash
ls
ls docs
```

## 5. Start infrastructure

```bash
docker compose up -d
```

Validate PostgreSQL:

```bash
docker ps
```

You should see containers for PostgreSQL and Redis.

The repository currently maps PostgreSQL to host port `5433` to avoid common local conflicts on `5432`.

## 6. Run the backend

Create a virtual environment and install the current backend dependencies:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

Apply migrations and seed demo data:

```bash
cd backend
alembic upgrade head
python -m app.db.seed
cd ..
```

Seeded demo credentials:

- owner: `owner@example.com`
- viewer: `viewer@example.com`
- password: `grounded-demo`

Run the backend:

```bash
uvicorn app.main:app --reload --app-dir backend --port 8000
```

Open a second backend terminal and run the ingestion worker:

```bash
source backend/.venv/bin/activate
python -m app.workers.run
```

Validate:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "environment": "development",
  "timestamp": "2026-05-11T00:00:00+00:00",
  "checks": {
    "database": {"status": "ok", "latency_ms": 3.2},
    "redis": {"status": "ok", "latency_ms": 1.4}
  }
}
```

## 7. Run the frontend

Open a new terminal in the project root:

```bash
cd frontend
npm install
npm run dev
```

Validate:

Open:

```text
http://localhost:3000
```

After login, the current document-management screen is available at:

```text
http://localhost:3000/app/documents
```

That screen now shows upload status, ingestion logs, chunk preview, and retry for failed jobs.

The current chat workspace is available at:

```text
http://localhost:3000/app/chat
```

The current evaluation workspace is available at:

```text
http://localhost:3000/app/evaluations
```

The current operational dashboard is available at:

```text
http://localhost:3000/app
```

That dashboard now shows document status cards, recent ingestion activity, your recent chat questions, the latest evaluation snapshot, and live health diagnostics for PostgreSQL and Redis.

Release-readiness smoke flow:

```bash
source backend/.venv/bin/activate
python scripts/demo_smoke.py --base-url http://localhost:8000
```

That command verifies login, upload, ingestion completion, grounded answer generation, and citation return against the running local stack.

The demo seed now creates sample processed documents and a 10-question golden evaluation set for the demo workspace.

Embedding defaults for local development:

- `EMBEDDING_PROVIDER=local`
- `EMBEDDING_MODEL=local-hash-1536`

If you want to use a real OpenAI-compatible embeddings endpoint later, set:

- `EMBEDDING_PROVIDER=openai_compatible`
- `EMBEDDING_API_KEY=<your key>`
- `EMBEDDING_BASE_URL=<provider base url>`

Answer-generation defaults for local development:

- `LLM_PROVIDER=local`
- `CHAT_MODEL=local-grounded-answerer`

If you want to use a real OpenAI-compatible chat endpoint later, set:

- `LLM_PROVIDER=openai_compatible`
- `LLM_API_KEY=<your key>`
- `LLM_BASE_URL=<provider base url>`

## 8. Configure environment variables

From project root:

```bash
cp .env.example .env
```

Edit `.env` and set real values only locally.

Do not commit `.env`.

## 9. Suggested backend folder structure

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── prompts/
│   ├── services/
│   ├── workers/
│   └── main.py
├── pyproject.toml
├── requirements.txt
├── tests/
└── .venv/
```

## 10. Suggested frontend folder structure

```text
frontend/src/
├── app/
├── components/
├── features/
├── lib/
└── types/
```

## 11. Initial commit

From project root:

```bash
git add .
git commit -m "Add initial documentation and project foundation"
```

## 12. Connect to GitHub

After creating the GitHub repository:

```bash
git remote add origin git@github.com:<your-user>/grounded-document-assistant.git
git branch -M main
git push -u origin main
```

## 13. Final local checklist

- [ ] Repository created inside WSL.
- [ ] Docker containers running.
- [ ] Migrations applied.
- [ ] Demo seed loaded.
- [ ] Backend healthcheck working with PostgreSQL and Redis diagnostics.
- [ ] Ingestion worker running.
- [ ] Frontend running.
- [ ] `.env.example` committed.
- [ ] `.env` ignored.
- [ ] Initial commit created.
- [ ] Remote repository connected.

## 14. Next implementation steps

After the local foundation works, continue in this order:

1. dashboard and observability;
2. testing and hardening;
3. deployment.
