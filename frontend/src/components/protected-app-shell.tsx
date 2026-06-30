"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { API_BASE_URL, apiRequest } from "@/lib/api";
import {
  clearStoredAuth,
  getStoredToken,
  getStoredWorkspaceId,
  setStoredWorkspaceId,
} from "@/lib/auth-storage";
import { ActiveWorkspaceResponse, AuthUser } from "@/types/auth";
import { DashboardSummaryResponse } from "@/types/dashboard";
import { HealthResponse } from "@/types/health";

export function ProtectedAppShell() {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [activeWorkspace, setActiveWorkspace] =
    useState<ActiveWorkspaceResponse | null>(null);
  const [dashboard, setDashboard] = useState<DashboardSummaryResponse | null>(
    null,
  );
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchHealth(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE_URL}/health`);
    const payload = (await response.json()) as HealthResponse;

    if (response.status !== 200 && response.status !== 503) {
      throw new Error("Could not load health diagnostics.");
    }

    return payload;
  }

  useEffect(() => {
    async function load() {
      const token = getStoredToken();
      if (!token) {
        router.replace("/login");
        return;
      }

      try {
        const currentUser = await apiRequest<AuthUser>("/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setUser(currentUser);

        const chosenWorkspaceId =
          getStoredWorkspaceId() ?? currentUser.memberships[0]?.workspace_id;

        if (chosenWorkspaceId) {
          setStoredWorkspaceId(chosenWorkspaceId);
          const [workspace, dashboardSummary, healthSummary] = await Promise.all([
            apiRequest<ActiveWorkspaceResponse>("/workspaces/active", {
              headers: {
                Authorization: `Bearer ${token}`,
                "X-Workspace-Id": chosenWorkspaceId,
              },
            }),
            apiRequest<DashboardSummaryResponse>("/dashboard", {
              headers: {
                Authorization: `Bearer ${token}`,
                "X-Workspace-Id": chosenWorkspaceId,
              },
            }),
            fetchHealth(),
          ]);
          setActiveWorkspace(workspace);
          setDashboard(dashboardSummary);
          setHealth(healthSummary);
        } else {
          setHealth(await fetchHealth());
        }
      } catch (requestError) {
        clearStoredAuth();
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Could not load the workspace dashboard.",
        );
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [router]);

  async function refreshWorkspaceDashboard(
    workspaceId: string,
    token: string,
  ): Promise<void> {
    const [workspace, dashboardSummary, healthSummary] = await Promise.all([
      apiRequest<ActiveWorkspaceResponse>("/workspaces/active", {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-Id": workspaceId,
        },
      }),
      apiRequest<DashboardSummaryResponse>("/dashboard", {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-Id": workspaceId,
        },
      }),
      fetchHealth(),
    ]);

    setActiveWorkspace(workspace);
    setDashboard(dashboardSummary);
    setHealth(healthSummary);
  }

  async function handleWorkspaceChange(workspaceId: string) {
    const token = getStoredToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    try {
      setError(null);
      setStoredWorkspaceId(workspaceId);
      await refreshWorkspaceDashboard(workspaceId, token);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not switch workspaces.",
      );
    }
  }

  function handleSignOut() {
    clearStoredAuth();
    router.replace("/login");
  }

  if (loading) {
    return (
      <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 text-sm text-slate-700 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
        Loading your dashboard...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="rounded-[1.75rem] border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        {error ?? "Authentication state is missing."}
      </div>
    );
  }

  const metricCards = [
    {
      label: "Total documents",
      value: String(dashboard?.document_metrics.total_documents ?? 0),
      tone: "bg-white/80",
    },
    {
      label: "Processed",
      value: String(dashboard?.document_metrics.processed_documents ?? 0),
      tone: "bg-[#e9f7f4]",
    },
    {
      label: "Failed",
      value: String(dashboard?.document_metrics.failed_documents ?? 0),
      tone: "bg-[#fff0ea]",
    },
    {
      label: "Your questions",
      value: String(dashboard?.usage_metrics.total_questions ?? 0),
      tone: "bg-[#eef5fb]",
    },
    {
      label: "Total tokens",
      value: formatCount(dashboard?.usage_metrics.total_tokens ?? 0),
      tone: "bg-white/80",
    },
    {
      label: "Latest eval pass rate",
      value:
        dashboard?.latest_evaluation_run?.pass_rate !== null &&
        dashboard?.latest_evaluation_run?.pass_rate !== undefined
          ? `${Math.round(dashboard.latest_evaluation_run.pass_rate * 100)}%`
          : activeWorkspace?.role === "owner" || activeWorkspace?.role === "admin"
            ? "No runs yet"
            : "Restricted",
      tone: "bg-[#f5f0ff]",
    },
  ];

  return (
    <div className="grid gap-6">
      {error ? (
        <div className="rounded-[1.4rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <section className="overflow-hidden rounded-[1.9rem] border border-border bg-[#13212f] shadow-[0_20px_70px_rgba(19,33,47,0.18)]">
        <div className="grid gap-6 p-6 lg:grid-cols-[1.35fr_0.65fr] lg:p-8">
          <div className="space-y-5 text-slate-100">
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-teal-200">
                Workspace dashboard
              </p>
              <h1 className="max-w-2xl text-3xl font-semibold text-white lg:text-4xl">
                Grounded document operations at a glance
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-slate-300">
                Review document readiness, recent grounded questions, evaluation
                quality, and service health without digging through the
                database.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link
                className="inline-flex items-center justify-center rounded-full bg-white px-5 py-3 text-sm font-semibold text-[#13212f] transition hover:bg-slate-100"
                href="/app/documents"
              >
                Documents
              </Link>
              <Link
                className="inline-flex items-center justify-center rounded-full border border-white/10 bg-[rgba(255,255,255,0.08)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[rgba(255,255,255,0.14)]"
                href="/app/chat"
              >
                Chat workspace
              </Link>
              <Link
                className="inline-flex items-center justify-center rounded-full border border-white/10 bg-[rgba(255,255,255,0.08)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[rgba(255,255,255,0.14)]"
                href="/app/evaluations"
              >
                Evaluations
              </Link>
            </div>
          </div>

          <div className="rounded-[1.6rem] border border-white/10 bg-[rgba(255,255,255,0.06)] p-5 text-slate-100">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">
                  Signed in
                </p>
                <p className="mt-2 text-lg font-semibold text-white">{user.name}</p>
                <p className="text-sm text-slate-300">{user.email}</p>
              </div>
              <button
                className="inline-flex items-center justify-center rounded-full border border-white/10 bg-[rgba(255,255,255,0.08)] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[rgba(255,255,255,0.14)]"
                onClick={handleSignOut}
                type="button"
              >
                Sign out
              </button>
            </div>

            <div className="mt-5 rounded-2xl border border-white/10 bg-[#0e1a26] px-4 py-4">
              <label className="block space-y-2">
                <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">
                  Active workspace
                </span>
                <select
                  className="w-full rounded-2xl border border-white/10 bg-[rgba(255,255,255,0.06)] px-4 py-3 text-sm text-white outline-none transition focus:border-teal-300"
                  onChange={(event) =>
                    void handleWorkspaceChange(event.target.value)
                  }
                  value={activeWorkspace?.workspace_id ?? ""}
                >
                  {user.memberships.map((membership) => (
                    <option
                      key={membership.workspace_id}
                      value={membership.workspace_id}
                    >
                      {membership.workspace.name} ({membership.role})
                    </option>
                  ))}
                </select>
              </label>
              {activeWorkspace ? (
                <div className="mt-4 space-y-1 text-sm text-slate-300">
                  <p className="font-semibold text-white">
                    {activeWorkspace.workspace.name}
                  </p>
                  <p>
                    Role:{" "}
                    <span className="font-semibold capitalize">
                      {activeWorkspace.role}
                    </span>
                  </p>
                  <p>
                    Slug:{" "}
                    <span className="font-mono text-slate-100">
                      {activeWorkspace.workspace.slug}
                    </span>
                  </p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        {metricCards.map((metric) => (
          <div
            key={metric.label}
            className={`rounded-[1.5rem] border border-border ${metric.tone} px-4 py-5 shadow-[0_14px_40px_rgba(19,33,47,0.08)]`}
          >
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              {metric.label}
            </p>
            <p className="mt-3 text-2xl font-semibold text-foreground">
              {metric.value}
            </p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="grid gap-6">
          <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
                  Recent questions
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-foreground">
                  Your latest grounded asks
                </h2>
              </div>
              <Link
                className="text-sm font-semibold text-accent transition hover:text-accent-strong"
                href="/app/chat"
              >
                Open chat
              </Link>
            </div>

            <div className="mt-5 space-y-3">
              {dashboard?.recent_questions.length ? (
                dashboard.recent_questions.map((question) => (
                  <Link
                    key={question.id}
                    className="block rounded-2xl border border-border bg-white/80 px-4 py-4 transition hover:bg-white"
                    href="/app/chat"
                  >
                    <p className="text-sm font-semibold text-foreground">
                      {question.content}
                    </p>
                    <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {formatDateTime(question.created_at)}
                    </p>
                  </Link>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-border px-4 py-6 text-sm text-slate-600">
                  No chat questions yet in this account. Ask the first grounded
                  question from the chat workspace.
                </div>
              )}
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
                  Ingestion feed
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-foreground">
                  Latest processing events
                </h2>
              </div>
              <Link
                className="text-sm font-semibold text-accent transition hover:text-accent-strong"
                href="/app/documents"
              >
                Open documents
              </Link>
            </div>

            <div className="mt-5 space-y-3">
              {dashboard?.recent_ingestion_logs.length ? (
                dashboard.recent_ingestion_logs.map((entry) => (
                  <div
                    key={entry.id}
                    className="rounded-2xl border border-border bg-white/80 px-4 py-4"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-semibold text-foreground">
                        {entry.document_title}
                      </p>
                      <span
                        className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${
                          entry.status === "success"
                            ? "bg-[#e9f7f4] text-[#0b5c56]"
                            : entry.status === "failed"
                              ? "bg-[#fff0ea] text-[#b45309]"
                              : "bg-[#edf4f8] text-[#1f4f72]"
                        }`}
                      >
                        {entry.status}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-700">
                      <span className="font-semibold capitalize">{entry.step}</span>
                      {entry.message ? ` · ${entry.message}` : ""}
                    </p>
                    <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {formatDateTime(entry.created_at)}
                    </p>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-border px-4 py-6 text-sm text-slate-600">
                  No ingestion events yet for this workspace.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-6">
          <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
              System health
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-foreground">
              Service diagnostics
            </h2>

            <div className="mt-5 grid gap-4">
              {health ? (
                <>
                  <HealthCard
                    detail={health.checks.database.detail}
                    label="Database"
                    latency={health.checks.database.latency_ms}
                    status={health.checks.database.status}
                  />
                  <HealthCard
                    detail={health.checks.redis.detail}
                    label="Redis"
                    latency={health.checks.redis.latency_ms}
                    status={health.checks.redis.status}
                  />
                  <div className="rounded-2xl border border-border bg-white/80 px-4 py-4 text-sm text-slate-700">
                    <p>
                      Overall status:{" "}
                      <span className="font-semibold capitalize text-foreground">
                        {health.status}
                      </span>
                    </p>
                    <p className="mt-1">
                      Environment:{" "}
                      <span className="font-semibold text-foreground">
                        {health.environment}
                      </span>
                    </p>
                    <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      Checked {formatDateTime(health.timestamp)}
                    </p>
                  </div>
                </>
              ) : (
                <div className="rounded-2xl border border-dashed border-border px-4 py-6 text-sm text-slate-600">
                  Health diagnostics were not available.
                </div>
              )}
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
                  Evaluation snapshot
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-foreground">
                  Latest quality run
                </h2>
              </div>
              <Link
                className="text-sm font-semibold text-accent transition hover:text-accent-strong"
                href="/app/evaluations"
              >
                Open evaluations
              </Link>
            </div>

            {dashboard?.latest_evaluation_run ? (
              <div className="mt-5 rounded-2xl border border-border bg-white/80 px-4 py-4">
                <p className="text-sm font-semibold text-foreground">
                  {dashboard.latest_evaluation_run.evaluation_set_name}
                </p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <SnapshotMetric
                    label="Pass rate"
                    value={
                      dashboard.latest_evaluation_run.pass_rate !== null
                        ? `${Math.round(dashboard.latest_evaluation_run.pass_rate * 100)}%`
                        : "—"
                    }
                  />
                  <SnapshotMetric
                    label="Average score"
                    value={
                      dashboard.latest_evaluation_run.average_score !== null
                        ? dashboard.latest_evaluation_run.average_score.toFixed(2)
                        : "—"
                    }
                  />
                  <SnapshotMetric
                    label="Passed questions"
                    value={
                      dashboard.latest_evaluation_run.passed_questions !== null
                        ? String(dashboard.latest_evaluation_run.passed_questions)
                        : "—"
                    }
                  />
                  <SnapshotMetric
                    label="Total questions"
                    value={
                      dashboard.latest_evaluation_run.total_questions !== null
                        ? String(dashboard.latest_evaluation_run.total_questions)
                        : "—"
                    }
                  />
                </div>
                <p className="mt-4 text-xs uppercase tracking-[0.16em] text-slate-500">
                  {formatDateTime(dashboard.latest_evaluation_run.created_at)}
                </p>
              </div>
            ) : (
              <div className="mt-5 rounded-2xl border border-dashed border-border px-4 py-6 text-sm text-slate-600">
                {activeWorkspace?.role === "owner" || activeWorkspace?.role === "admin"
                  ? "No evaluation runs yet for this workspace."
                  : "Evaluation history is reserved for owner and admin roles."}
              </div>
            )}
          </div>

          <div className="rounded-[1.75rem] border border-border bg-[#fffaf2] p-6 shadow-[0_16px_60px_rgba(19,33,47,0.08)]">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
              Workspace pulse
            </p>
            <div className="mt-4 grid gap-3">
              <SnapshotMetric
                label="Pending docs"
                value={String(dashboard?.document_metrics.pending_documents ?? 0)}
              />
              <SnapshotMetric
                label="Processing docs"
                value={String(dashboard?.document_metrics.processing_documents ?? 0)}
              />
              <SnapshotMetric
                label="Disabled docs"
                value={String(dashboard?.document_metrics.disabled_documents ?? 0)}
              />
              <SnapshotMetric
                label="Conversations"
                value={String(dashboard?.usage_metrics.total_conversations ?? 0)}
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function HealthCard({
  label,
  status,
  latency,
  detail,
}: {
  label: string;
  status: string;
  latency: number;
  detail?: string;
}) {
  const healthy = status === "ok";

  return (
    <div className="rounded-2xl border border-border bg-white/80 px-4 py-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-foreground">{label}</p>
        <span
          className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${
            healthy
              ? "bg-[#e9f7f4] text-[#0b5c56]"
              : "bg-[#fff0ea] text-[#b45309]"
          }`}
        >
          {status}
        </span>
      </div>
      <p className="mt-2 text-sm text-slate-700">{latency} ms</p>
      {detail ? <p className="mt-2 text-sm text-slate-600">{detail}</p> : null}
    </div>
  );
}

function SnapshotMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-white/80 px-4 py-4">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-lg font-semibold text-foreground">{value}</p>
    </div>
  );
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}
