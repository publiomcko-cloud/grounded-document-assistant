# Local Development Environment Architecture — Grounded Document Assistant

## 1. Environment strategy

The local environment should be simple, reproducible, and close enough to production to avoid surprises. The recommended setup uses:

- Windows as the host operating system if needed;
- WSL Ubuntu as the development environment;
- Docker Desktop for PostgreSQL, pgvector, and Redis;
- VS Code connected to WSL;
- separate frontend and backend processes;
- environment variables stored in `.env` files.

## 2. Applications used

Recommended tools:

- Git;
- GitHub CLI or SSH authentication;
- VS Code;
- WSL Ubuntu;
- Docker Desktop with WSL integration;
- Node.js LTS or current stable;
- Python 3.11+;
- PostgreSQL client tools;
- curl or HTTPie;
- optional API client such as Insomnia, Postman, or Bruno.

## 3. Role of the operating system

The host operating system should only provide the desktop environment and Docker Desktop. Development commands should be executed inside WSL Ubuntu to avoid path, permission, and dependency conflicts.

## 4. Role of the Linux terminal

The Linux terminal is where the project should be created, installed, executed, tested, and committed.

Use it for:

- creating folders;
- running Git commands;
- installing Node and Python dependencies;
- running Docker Compose;
- running backend and frontend servers;
- executing tests;
- creating commits.

## 5. Where to store the project

Recommended location inside WSL:

```bash
~/projects/grounded-document-assistant
```

Avoid developing directly inside mounted Windows paths such as `/mnt/c/...` because file watching, permissions, and performance may be worse.

## 6. Process layout

```text
WSL Ubuntu
  ~/projects/grounded-document-assistant
    frontend/    -> Next.js dev server
    backend/     -> FastAPI dev server
    docs/        -> documentation
    docker-compose.yml

Docker Desktop
  postgres + pgvector
  redis
```

## 7. Local runtime flow

1. Docker starts PostgreSQL and Redis.
2. Backend connects to PostgreSQL and Redis.
3. Worker connects to Redis and PostgreSQL.
4. Frontend calls backend API.
5. Backend calls LLM and embedding providers.
6. Uploaded files are stored locally in a private storage folder.

## 8. Good practices

- Keep `.env.example` updated.
- Never commit real API keys.
- Run migrations before starting the backend.
- Keep backend and frontend logs visible in separate terminals.
- Use seed data for demo flows.
- Write tests for permission boundaries.
- Keep docs updated after major technical changes.

## 9. Common mistakes

- Running some commands in Windows PowerShell and others in WSL without understanding path differences.
- Developing inside `/mnt/c` and facing slow file watching.
- Forgetting Docker Desktop WSL integration.
- Exposing uploaded files through the public frontend.
- Calling the LLM provider directly from the frontend.
- Building RAG without citations or evaluation.

## 10. Recommended terminal split

Use four terminals:

1. `docker compose up` or container logs.
2. backend API server.
3. ingestion worker.
4. frontend dev server.

## 11. Environment variables

Use one `.env` file for local development at the repository root, or separate files if the final implementation needs it.

Minimum variables:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `FILE_STORAGE_PATH`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `CHAT_MODEL`
- `EMBEDDING_MODEL`
- `MAX_UPLOAD_MB`
