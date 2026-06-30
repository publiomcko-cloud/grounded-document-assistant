import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-10 sm:px-10 lg:px-12">
      <section className="overflow-hidden rounded-[2rem] border border-border bg-surface-strong shadow-[0_20px_80px_rgba(19,33,47,0.12)] backdrop-blur">
        <div className="grid gap-10 px-6 py-8 sm:px-10 sm:py-12 lg:grid-cols-[1.4fr_0.9fr] lg:px-12">
          <div className="space-y-8">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-white/70 px-4 py-2 text-sm font-medium text-accent-strong">
              <span className="h-2 w-2 rounded-full bg-accent" />
              Foundation and data milestones are in place
            </div>

            <div className="space-y-5">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-warm">
                Grounded Document Assistant
              </p>
              <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
                Trustworthy document answers, built on retrieval and citations.
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-slate-700">
                The project now has a backend healthcheck, a real PostgreSQL
                schema with Alembic, seeded demo users, and the first
                authentication screens wired to JWT-protected backend endpoints.
              </p>
            </div>

            <div className="flex flex-col gap-4 sm:flex-row">
              <Link
                className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-3 text-sm font-semibold text-white transition hover:bg-accent-strong"
                href="/login"
              >
                Open login
              </Link>
              <Link
                className="inline-flex items-center justify-center rounded-full border border-border bg-white/75 px-6 py-3 text-sm font-semibold text-foreground transition hover:bg-white"
                href="/register"
              >
                Create account
              </Link>
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-border bg-[#13212f] p-6 text-slate-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-200">
              Foundation checklist
            </p>
            <div className="mt-6 space-y-4">
              {[
                "FastAPI backend skeleton with routed /health endpoint",
                "PostgreSQL schema, pgvector extension, and Alembic migration flow",
                "JWT auth endpoints plus current-user and workspace membership loading",
                "Next.js login, register, and protected workspace shell",
                "Quality scripts for lint, build, format, and pytest",
                "Initial GitHub Actions workflow for backend and frontend checks",
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3"
                >
                  <span className="mt-1 h-2.5 w-2.5 rounded-full bg-teal-300" />
                  <p className="text-sm leading-6 text-slate-200">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 py-8 md:grid-cols-3">
        {[
          {
            title: "Backend",
            body: "FastAPI now serves auth, current-user, and workspace-resolution endpoints on top of the core schema and migration layer.",
          },
          {
            title: "Frontend",
            body: "Next.js now includes login, registration, demo credentials, token storage, and a protected app shell for milestone validation.",
          },
          {
            title: "Infra",
            body: "Docker Compose runs PostgreSQL on 5433 and Redis on 6379, with Alembic and seed commands ready for local bootstrap.",
          },
        ].map((card) => (
          <article
            key={card.title}
            className="rounded-[1.5rem] border border-border bg-surface px-6 py-5 shadow-[0_12px_40px_rgba(19,33,47,0.08)] backdrop-blur"
          >
            <h2 className="text-lg font-semibold text-foreground">
              {card.title}
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-700">{card.body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
