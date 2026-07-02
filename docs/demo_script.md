# Demo Script - Grounded Document Assistant

This script is designed for a 60 to 180 second portfolio walkthrough. Use only synthetic demo data and avoid showing browser devtools, tokens, environment variables, database passwords, or private documents.

## Demo Links

```text
Frontend: https://grounded-document-assistant.vercel.app
Backend health: https://grounded-document-assistant-api.onrender.com/health
API docs: https://grounded-document-assistant-api.onrender.com/docs
```

## Demo Credentials

```text
Owner
owner@example.com
grounded-demo

Viewer
viewer@example.com
grounded-demo
```

## 60-180 Second Video Flow

### 0-10s - Opening

Grounded Document Assistant is a full-stack AI/RAG portfolio project for uploading documents, retrieving relevant chunks, and answering questions with source citations.

It demonstrates a complete applied AI workflow: authentication, document ingestion, vector retrieval, permission-aware access, grounded answers, and evaluation.

### 10-25s - Login And Dashboard

Open the public frontend and click `Open login`.

Click `Use owner demo`, submit the form, and show the dashboard.

Point out:

- PostgreSQL and Redis health checks.
- Document metrics.
- Recent questions and ingestion activity.
- Evaluation snapshot for owner/admin users.

### 25-55s - Documents And Ingestion

Open `/app/documents`.

Show the seeded demo documents:

- `Refund Policy`
- `Warranty Guide`
- `Support Escalation Playbook`
- `Finance Approval Matrix`

Open a document and show extracted content, chunks, token counts, and ingestion logs.

Optional upload path:

1. Upload a small `.txt` document.
2. Use visibility `workspace`.
3. Wait for the document to become `processed`.
4. Show that chunks were created.

Explain that the public demo processes uploads inline on the Render backend to avoid a paid worker dependency.

### 55-90s - Chat With Citations

Open `/app/chat`.

Ask:

```text
What is the refund deadline?
```

Expected answer:

- Mentions a 30-day refund window.
- Includes at least one citation to `Refund Policy`.

Then ask:

```text
What information is required for a warranty claim?
```

Expected answer:

- Mentions proof of purchase and product serial number.
- Includes a citation to `Warranty Guide`.

Point out that answers are grounded in retrieved chunks rather than free-form chatbot memory.

### 90-120s - Permission-Aware Retrieval

Explain that the demo has owner and viewer accounts.

Use this talking point:

```text
The viewer account can access allowed workspace content, but restricted and private documents are filtered before retrieval and citation.
```

If time allows, sign in as the viewer and ask about private finance approval rules. The expected behavior is no citation to private owner-only content.

### 120-150s - Evaluations

Open `/app/evaluations`.

Run the seeded evaluation set:

```text
Grounded Demo Golden Set
```

Show:

- Golden questions.
- Expected answer notes.
- Retrieved source references.
- Score summary.
- Result rows.

Explain that this makes the project stronger than a basic chatbot demo because retrieval and answer quality can be checked repeatedly.

### 150-180s - API And Close

Open the FastAPI docs:

```text
https://grounded-document-assistant-api.onrender.com/docs
```

Briefly show the main API areas:

- auth
- documents
- retrieval
- chat
- evaluations
- dashboard

Close with:

```text
Grounded Document Assistant is deployed on Vercel, Render, Supabase PostgreSQL, and Render Key Value. It is a portfolio-ready example of practical full-stack AI engineering with citations, permissions, and evaluation.
```

## Click Path

1. Open `https://grounded-document-assistant.vercel.app`.
2. Click `Open login`.
3. Click `Use owner demo`.
4. Submit the login form.
5. Review `/app`.
6. Open `/app/documents`.
7. Open a seeded document and show content/chunks/logs.
8. Open `/app/chat`.
9. Ask `What is the refund deadline?`.
10. Inspect citation cards.
11. Open `/app/evaluations`.
12. Run `Grounded Demo Golden Set`.
13. Open `/docs` on the backend API.

## Fallback Plan

Render free-tier services may cold start after inactivity.

If the first login or API request is slow:

1. Open `https://grounded-document-assistant-api.onrender.com/health`.
2. Wait until it returns `status: ok`.
3. Refresh the frontend and retry login.

If upload processing is slow:

1. Use seeded documents instead of uploading a new file.
2. Continue the demo with the seeded refund and warranty questions.

If an evaluation run takes too long:

1. Show the seeded evaluation set.
2. Explain the run flow.
3. Use existing result rows if available.

## Safety Notes

- Use only the seeded synthetic documents or clearly synthetic test files.
- Do not upload real customer, legal, medical, financial, or company documents.
- Do not show secrets, environment variables, JWT tokens, database URLs, or platform dashboards containing private values.
- The local deterministic AI providers are demo providers and should not be presented as production model quality.
