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

## 6. Create backend skeleton

Recommended FastAPI setup:

```bash
mkdir backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic sqlalchemy alembic psycopg[binary] redis python-jose passlib[bcrypt] python-multipart
pip freeze > requirements.txt
mkdir -p app/api app/core app/db app/models app/services app/workers app/prompts tests
 touch app/__init__.py app/main.py
```

Create a minimal healthcheck in `backend/app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Grounded Document Assistant API")

@app.get("/health")
def health():
    return {"status": "ok"}
```

Run:

```bash
uvicorn app.main:app --reload --port 8000
```

Validate:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## 7. Create frontend skeleton

Open a new terminal in the project root:

```bash
npx create-next-app@latest frontend --ts --eslint --tailwind --app --src-dir --import-alias "@/*"
cd frontend
npm run dev
```

Validate:

Open:

```text
http://localhost:3000
```

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
├── tests/
└── requirements.txt
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
- [ ] Documentation files copied.
- [ ] Docker containers running.
- [ ] Backend healthcheck working.
- [ ] Frontend running.
- [ ] `.env.example` committed.
- [ ] `.env` ignored.
- [ ] Initial commit created.
- [ ] Remote repository connected.

## 14. Next implementation steps

After the local foundation works, continue in this order:

1. database migrations;
2. user model;
3. authentication;
4. workspace model;
5. document upload;
6. ingestion worker;
7. chunking;
8. embeddings;
9. retrieval;
10. chat with citations;
11. evaluation module;
12. deployment.
