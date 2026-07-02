"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiRequest } from "@/lib/api";
import {
  clearStoredAuth,
  getStoredToken,
  getStoredWorkspaceId,
} from "@/lib/auth-storage";
import { ActiveWorkspaceResponse } from "@/types/auth";
import {
  EvaluationRunDetail,
  EvaluationSetCreateRequest,
  EvaluationSetDetail,
  EvaluationSetSummary,
} from "@/types/evaluation";

type DraftQuestion = {
  id: string;
  question: string;
  expected_answer_notes: string;
};

export function EvaluationWorkspace() {
  const router = useRouter();
  const [workspace, setWorkspace] = useState<ActiveWorkspaceResponse | null>(
    null,
  );
  const [sets, setSets] = useState<EvaluationSetSummary[]>([]);
  const [selectedSet, setSelectedSet] = useState<EvaluationSetDetail | null>(
    null,
  );
  const [selectedRun, setSelectedRun] = useState<EvaluationRunDetail | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newSetName, setNewSetName] = useState("");
  const [newSetDescription, setNewSetDescription] = useState("");
  const [draftQuestions, setDraftQuestions] = useState<DraftQuestion[]>([
    createDraftQuestion(),
  ]);

  useEffect(() => {
    async function load() {
      const token = getStoredToken();
      const workspaceId = getStoredWorkspaceId();

      if (!token || !workspaceId) {
        router.replace("/login");
        return;
      }

      try {
        const activeWorkspace = await apiRequest<ActiveWorkspaceResponse>(
          "/workspaces/active",
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "X-Workspace-Id": workspaceId,
            },
          },
        );
        setWorkspace(activeWorkspace);

        const loadedSets = await apiRequest<EvaluationSetSummary[]>(
          "/evaluations/sets",
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "X-Workspace-Id": workspaceId,
            },
          },
        );
        setSets(loadedSets);
        if (loadedSets[0]) {
          await openSet(loadedSets[0].id, token, workspaceId);
        }
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Could not load evaluations.",
        );
        clearStoredAuth();
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [router]);

  async function openSet(
    evaluationSetId: string,
    tokenOverride?: string,
    workspaceOverride?: string,
  ) {
    const token = tokenOverride ?? getStoredToken();
    const workspaceId = workspaceOverride ?? getStoredWorkspaceId();
    if (!token || !workspaceId) {
      return;
    }

    try {
      setError(null);
      const detail = await apiRequest<EvaluationSetDetail>(
        `/evaluations/sets/${evaluationSetId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-Id": workspaceId,
          },
        },
      );
      setSelectedSet(detail);
      setSelectedRun(null);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not load the evaluation set.",
      );
    }
  }

  async function openRun(runId: string) {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId) {
      return;
    }

    try {
      setError(null);
      const detail = await apiRequest<EvaluationRunDetail>(
        `/evaluations/runs/${runId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-Id": workspaceId,
          },
        },
      );
      setSelectedRun(detail);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not load the evaluation run.",
      );
    }
  }

  async function runEvaluation() {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId || !selectedSet) {
      return;
    }

    setRunning(true);
    setError(null);
    try {
      const run = await apiRequest<EvaluationRunDetail>("/evaluations/runs", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-Id": workspaceId,
        },
        body: JSON.stringify({
          evaluation_set_id: selectedSet.id,
          top_k: 5,
        }),
      });
      setSelectedRun(run);
      await openSet(selectedSet.id, token, workspaceId);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Evaluation run failed",
      );
    } finally {
      setRunning(false);
    }
  }

  function addDraftQuestion() {
    setDraftQuestions((current) => [...current, createDraftQuestion()]);
  }

  function removeDraftQuestion(questionId: string) {
    setDraftQuestions((current) =>
      current.length === 1
        ? current
        : current.filter((question) => question.id !== questionId),
    );
  }

  function updateDraftQuestion(
    questionId: string,
    field: "question" | "expected_answer_notes",
    value: string,
  ) {
    setDraftQuestions((current) =>
      current.map((question) =>
        question.id === questionId ? { ...question, [field]: value } : question,
      ),
    );
  }

  async function createEvaluationSet() {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId) {
      router.replace("/login");
      return;
    }

    const payload: EvaluationSetCreateRequest = {
      name: newSetName.trim(),
      description: newSetDescription.trim() || null,
      questions: draftQuestions
        .map((question) => ({
          question: question.question.trim(),
          expected_answer_notes: question.expected_answer_notes.trim(),
        }))
        .filter(
          (question) => question.question && question.expected_answer_notes,
        ),
    };

    if (!payload.name || payload.questions.length === 0) {
      setError(
        "Add a set name and at least one question with expected answer notes.",
      );
      return;
    }

    setCreating(true);
    setError(null);
    try {
      const createdSet = await apiRequest<EvaluationSetDetail>(
        "/evaluations/sets",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-Id": workspaceId,
          },
          body: JSON.stringify(payload),
        },
      );

      const loadedSets = await apiRequest<EvaluationSetSummary[]>(
        "/evaluations/sets",
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-Id": workspaceId,
          },
        },
      );
      setSets(loadedSets);
      setSelectedSet(createdSet);
      setSelectedRun(null);
      setNewSetName("");
      setNewSetDescription("");
      setDraftQuestions([createDraftQuestion()]);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not create the evaluation set.",
      );
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 text-sm text-slate-700 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
        Loading evaluation workspace...
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <section className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
              Evaluation
            </p>
            <h1 className="text-3xl font-semibold text-foreground">
              Golden-set quality checks
            </h1>
            <p className="text-sm leading-7 text-slate-700">
              Run the current retrieval and answer stack against seeded
              questions and inspect pass rates, answers, and retrieved sources.
            </p>
          </div>

          <Link
            className="inline-flex items-center justify-center rounded-full border border-border bg-white px-5 py-3 text-sm font-semibold text-foreground transition hover:bg-slate-50"
            href="/app"
          >
            Back to shell
          </Link>
        </div>
        <p className="mt-4 text-sm text-slate-700">
          Active workspace:{" "}
          <span className="font-semibold text-foreground">
            {workspace?.workspace.name}
          </span>
        </p>
      </section>

      <section className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
              Create evaluation set
            </p>
            <h2 className="text-2xl font-semibold text-foreground">
              Build a custom golden set
            </h2>
            <p className="text-sm leading-7 text-slate-700">
              Add your own evaluation questions and expected answer notes, then
              run the new set immediately from this page.
            </p>
          </div>
          <button
            className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-3 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-70"
            disabled={creating}
            onClick={() => void createEvaluationSet()}
            type="button"
          >
            {creating ? "Creating set..." : "Create evaluation set"}
          </button>
        </div>

        <div className="mt-6 grid gap-4">
          <label className="block space-y-2">
            <span className="text-sm font-medium text-foreground">
              Set name
            </span>
            <input
              className="w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
              onChange={(event) => setNewSetName(event.target.value)}
              placeholder="Day trading validation set"
              value={newSetName}
            />
          </label>

          <label className="block space-y-2">
            <span className="text-sm font-medium text-foreground">
              Description
            </span>
            <textarea
              className="min-h-24 w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
              onChange={(event) => setNewSetDescription(event.target.value)}
              placeholder="What this evaluation set is meant to validate"
              value={newSetDescription}
            />
          </label>
        </div>

        <div className="mt-6 space-y-4">
          {draftQuestions.map((question, index) => (
            <div
              className="rounded-2xl border border-border bg-white/80 px-4 py-4"
              key={question.id}
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-foreground">
                  Question {index + 1}
                </p>
                <button
                  className="rounded-full border border-border bg-white px-3 py-1 text-xs font-semibold text-foreground transition hover:bg-slate-50 disabled:opacity-50"
                  disabled={draftQuestions.length === 1}
                  onClick={() => removeDraftQuestion(question.id)}
                  type="button"
                >
                  Remove
                </button>
              </div>

              <div className="mt-4 grid gap-4">
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-foreground">
                    Prompt
                  </span>
                  <textarea
                    className="min-h-20 w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
                    onChange={(event) =>
                      updateDraftQuestion(
                        question.id,
                        "question",
                        event.target.value,
                      )
                    }
                    placeholder="What is the common risk model per trade?"
                    value={question.question}
                  />
                </label>

                <label className="block space-y-2">
                  <span className="text-sm font-medium text-foreground">
                    Expected answer notes
                  </span>
                  <textarea
                    className="min-h-24 w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
                    onChange={(event) =>
                      updateDraftQuestion(
                        question.id,
                        "expected_answer_notes",
                        event.target.value,
                      )
                    }
                    placeholder="Mention risking one percent or less of account equity."
                    value={question.expected_answer_notes}
                  />
                </label>
              </div>
            </div>
          ))}

          <button
            className="inline-flex items-center justify-center rounded-full border border-border bg-white px-5 py-3 text-sm font-semibold text-foreground transition hover:bg-slate-50"
            onClick={addDraftQuestion}
            type="button"
          >
            Add question
          </button>
        </div>

        {error ? (
          <p className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.95fr_1.35fr]">
        <div className="rounded-[1.75rem] border border-border bg-[#13212f] p-6 text-slate-100 shadow-[0_16px_60px_rgba(19,33,47,0.12)]">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-200">
              Evaluation sets
            </p>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-slate-200">
              {sets.length} total
            </span>
          </div>

          <div className="mt-6 space-y-3">
            {sets.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/20 bg-white/5 px-4 py-6 text-sm text-slate-300">
                No evaluation sets available in this workspace.
              </div>
            ) : (
              sets.map((setItem) => (
                <button
                  key={setItem.id}
                  className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-left transition hover:bg-white/10"
                  onClick={() => void openSet(setItem.id)}
                  type="button"
                >
                  <p className="text-sm font-semibold text-white">
                    {setItem.name}
                  </p>
                  <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                    {setItem.question_count} questions
                  </p>
                  {setItem.description ? (
                    <p className="mt-2 text-sm text-slate-300">
                      {setItem.description}
                    </p>
                  ) : null}
                </button>
              ))
            )}
          </div>
        </div>

        <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
          {selectedSet ? (
            <>
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
                    Selected set
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold text-foreground">
                    {selectedSet.name}
                  </h2>
                  <p className="mt-2 text-sm leading-7 text-slate-700">
                    {selectedSet.description || "No description provided."}
                  </p>
                </div>
                <button
                  className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-3 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-70"
                  disabled={running}
                  onClick={() => void runEvaluation()}
                  type="button"
                >
                  {running ? "Running evaluation..." : "Run evaluation"}
                </button>
              </div>

              {error ? (
                <p className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </p>
              ) : null}

              <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
                {[
                  ["Questions", String(selectedSet.questions.length)],
                  ["Recent runs", String(selectedSet.recent_runs.length)],
                  [
                    "Latest pass rate",
                    String(selectedRun?.score_summary?.pass_rate ?? "—"),
                  ],
                  [
                    "Latest avg score",
                    String(selectedRun?.score_summary?.average_score ?? "—"),
                  ],
                ].map(([label, value]) => (
                  <div
                    key={label}
                    className="rounded-2xl border border-border bg-white/80 px-4 py-4"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      {label}
                    </p>
                    <p className="mt-2 text-sm font-semibold text-foreground">
                      {value}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-6 rounded-2xl border border-border bg-white/80 px-4 py-4">
                <p className="text-sm font-semibold text-foreground">
                  Golden questions
                </p>
                <div className="mt-4 space-y-3">
                  {selectedSet.questions.map((question) => (
                    <div
                      key={question.id}
                      className="rounded-2xl border border-border px-4 py-4"
                    >
                      <p className="text-sm font-semibold text-foreground">
                        {question.question}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-700">
                        {question.expected_answer_notes}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6 rounded-2xl border border-border bg-white/80 px-4 py-4">
                <p className="text-sm font-semibold text-foreground">
                  Recent runs
                </p>
                <div className="mt-4 space-y-3">
                  {selectedSet.recent_runs.length === 0 ? (
                    <p className="rounded-2xl border border-dashed border-border px-4 py-4 text-sm text-slate-600">
                      No runs yet for this evaluation set.
                    </p>
                  ) : (
                    selectedSet.recent_runs.map((run) => (
                      <button
                        key={run.id}
                        className="w-full rounded-2xl border border-border px-4 py-4 text-left transition hover:bg-slate-50"
                        onClick={() => void openRun(run.id)}
                        type="button"
                      >
                        <p className="text-sm font-semibold text-foreground">
                          {new Date(run.created_at).toLocaleString()}
                        </p>
                        <p className="mt-1 text-sm text-slate-700">
                          Pass rate:{" "}
                          <span className="font-semibold">
                            {String(run.score_summary?.pass_rate ?? "—")}
                          </span>
                        </p>
                      </button>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-2xl border border-dashed border-border px-4 py-6 text-sm text-slate-600">
              Select an evaluation set to inspect questions and run results.
            </div>
          )}
        </div>
      </section>

      {selectedRun ? (
        <section className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
          <h2 className="text-2xl font-semibold text-foreground">
            Evaluation run results
          </h2>
          <p className="mt-2 text-sm leading-7 text-slate-700">
            {selectedRun.evaluation_set_name} · {selectedRun.model_name}
          </p>

          <div className="mt-6 space-y-4">
            {selectedRun.results.map((result) => (
              <div
                key={result.id}
                className="rounded-2xl border border-border bg-white/80 px-4 py-4"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <p className="text-sm font-semibold text-foreground">
                    {result.question}
                  </p>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${
                      result.passed
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {result.passed ? "pass" : "fail"}
                  </span>
                  <span className="text-xs text-slate-500">
                    score {result.score ?? 0}
                  </span>
                </div>
                <p className="mt-3 text-sm text-slate-700">
                  Expected: {result.expected_answer_notes}
                </p>
                <p className="mt-2 text-sm leading-7 text-slate-700">
                  Generated: {result.generated_answer}
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  Retrieved chunks: {result.retrieved_chunk_ids?.length ?? 0}
                  {result.notes ? ` · ${result.notes}` : ""}
                </p>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function createDraftQuestion(): DraftQuestion {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
    question: "",
    expected_answer_notes: "",
  };
}
