# Testing Strategy — Grounded Document Assistant

## 1. Testing objective

The testing strategy must prove that the system works as a grounded document assistant and does not leak restricted information.

The MVP does not need exhaustive enterprise-grade testing, but it must cover the flows that matter most:

- authentication;
- document upload;
- ingestion;
- retrieval;
- citations;
- permission boundaries;
- evaluation workflow.

## 2. Testing types

### Unit tests

Used for isolated logic:

- chunking strategy;
- prompt builder;
- citation builder;
- permission checks;
- retrieval score normalization;
- file validation.

### Integration tests

Used for API and database behavior:

- user registration and login;
- workspace access;
- document metadata creation;
- chunk storage;
- retrieval filtering;
- message and citation persistence.

### End-to-end tests

Used for core user flow:

1. login;
2. upload document;
3. wait for processing;
4. ask question;
5. receive answer with citation.

Can be implemented after core backend is stable.

### Evaluation tests

Used for RAG quality:

- golden questions;
- expected documents;
- expected answer notes;
- retrieved chunks;
- generated answer;
- pass/fail or score.

## 3. Critical flows to test

## Flow 1 — Authentication

Test cases:

- user can register;
- user can log in;
- invalid credentials fail;
- protected endpoint rejects unauthenticated request.

## Flow 2 — Workspace access

Test cases:

- user can access own workspace;
- user cannot access another workspace;
- role is loaded correctly.

## Flow 3 — Document upload

Test cases:

- valid PDF upload succeeds;
- invalid file type fails;
- file over size limit fails;
- document status starts as pending or processing.

## Flow 4 — Ingestion

Test cases:

- text extraction creates output;
- chunking creates ordered chunks;
- chunk metadata includes document and version;
- failed ingestion records error log.

## Flow 5 — Retrieval

Test cases:

- vector retrieval returns chunks from the correct workspace;
- keyword fallback works when vector result is weak;
- disabled documents are not retrieved;
- restricted documents are not retrieved by unauthorized users.

## Flow 6 — Answer generation

Test cases:

- answer uses retrieved context;
- answer has citations;
- citations refer to existing chunks;
- insufficient context returns safe response;
- model provider error is handled.

## Flow 7 — Evaluation

Test cases:

- golden set can be created or seeded;
- evaluation run stores results;
- retrieved chunks are stored;
- score summary is generated.

## 4. Minimum validation criteria

Before public demo:

- all authentication tests pass;
- upload validation tests pass;
- one ingestion test passes;
- one retrieval test passes;
- one permission leakage test passes;
- one answer-with-citation test passes;
- evaluation run works for at least 10 questions.

## 5. Suggested test commands

Backend:

```bash
cd backend
source .venv/bin/activate
pytest
```

Frontend:

```bash
cd frontend
npm test
npm run lint
```

End-to-end, if Playwright is added:

```bash
cd frontend
npx playwright test
```

## 6. Golden set example

Each golden question should include:

- question;
- expected answer notes;
- expected source document;
- expected page or section when available;
- pass/fail notes.

Example:

```text
Question: What is the refund deadline according to the sample policy?
Expected answer notes: The answer must mention the deadline and conditions.
Expected source: sample_refund_policy.pdf
Expected citation: page 2 or relevant chunk.
```

## 7. Testing priorities

Highest priority:

1. permission leakage prevention;
2. citation correctness;
3. document ingestion reliability;
4. retrieval quality;
5. authentication and workspace access.

Lower priority:

- visual regression;
- load testing;
- advanced prompt evaluation;
- cost optimization tests.
