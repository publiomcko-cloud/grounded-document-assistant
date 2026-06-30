# Grounded Document Assistant Frontend

This directory contains the Next.js App Router frontend for Grounded Document Assistant.

The frontend provides the portfolio demo interface for:

- authentication and demo-user login
- operational dashboard
- document upload and document detail review
- grounded chat with citations
- evaluation set creation and evaluation runs

## Local Development

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## Environment

The frontend uses one public API variable:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

For Vercel, set this value to the deployed Render backend URL.

## Validation

```bash
npm run lint
npm run typecheck
npm run format:check
npm run build
```
