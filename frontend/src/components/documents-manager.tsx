"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { apiFetch, apiRequest } from "@/lib/api";
import {
  clearStoredAuth,
  getStoredToken,
  getStoredWorkspaceId,
} from "@/lib/auth-storage";
import { ActiveWorkspaceResponse } from "@/types/auth";
import {
  DocumentChunkPreview,
  DocumentDetail,
  DocumentSummary,
  DocumentVisibility,
  IngestionLogEntry,
} from "@/types/documents";

const CAN_MANAGE_ROLES = new Set(["owner", "admin"]);
const CAN_UPLOAD_ROLES = new Set(["owner", "admin", "member"]);

export function DocumentsManager() {
  const router = useRouter();
  const [workspace, setWorkspace] = useState<ActiveWorkspaceResponse | null>(
    null,
  );
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedDocument, setSelectedDocument] =
    useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<DocumentVisibility>("workspace");
  const [file, setFile] = useState<File | null>(null);

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

        const workspaceDocuments = await apiRequest<DocumentSummary[]>(
          "/documents",
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "X-Workspace-Id": workspaceId,
            },
          },
        );
        setDocuments(workspaceDocuments);
      } catch (requestError) {
        clearStoredAuth();
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Could not load workspace documents.",
        );
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [router]);

  async function refreshDocuments() {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId) {
      return;
    }

    const workspaceDocuments = await apiRequest<DocumentSummary[]>(
      "/documents",
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-Id": workspaceId,
        },
      },
    );
    setDocuments(workspaceDocuments);
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();

    if (!token || !workspaceId || !file) {
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("title", title);
      formData.append("description", description);
      formData.append("visibility", visibility);
      formData.append("file", file);

      const response = await apiFetch("/documents", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-Id": workspaceId,
        },
        body: formData,
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? "Upload failed");
      }

      const createdDocument = (await response.json()) as DocumentDetail;
      setSelectedDocument(createdDocument);
      setTitle("");
      setDescription("");
      setVisibility("workspace");
      setFile(null);
      await refreshDocuments();
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Upload failed",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function openDocument(documentId: string) {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId) {
      return;
    }

    try {
      setError(null);
      const detail = await apiRequest<DocumentDetail>(
        `/documents/${documentId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-Id": workspaceId,
          },
        },
      );
      setSelectedDocument(detail);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not load document details.",
      );
    }
  }

  async function retryDocument(documentId: string) {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId) {
      return;
    }

    try {
      setError(null);
      const detail = await apiRequest<DocumentDetail>(
        `/documents/${documentId}/retry`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-Id": workspaceId,
          },
        },
      );
      setSelectedDocument(detail);
      await refreshDocuments();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not retry ingestion.",
      );
    }
  }

  async function disableDocument(documentId: string) {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId) {
      return;
    }

    try {
      setError(null);
      await apiRequest<DocumentDetail>(`/documents/${documentId}/disable`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-Id": workspaceId,
        },
      });
      await refreshDocuments();
      if (selectedDocument?.id === documentId) {
        await openDocument(documentId);
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not disable document.",
      );
    }
  }

  async function deleteDocument(documentId: string) {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId) {
      return;
    }

    try {
      setError(null);
      const response = await apiFetch(`/documents/${documentId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-Id": workspaceId,
        },
      });
      if (!response.ok) {
        throw new Error("Delete failed");
      }

      if (selectedDocument?.id === documentId) {
        setSelectedDocument(null);
      }
      await refreshDocuments();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not delete document.",
      );
    }
  }

  if (loading) {
    return (
      <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 text-sm text-slate-700 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
        Loading documents...
      </div>
    );
  }

  const canUpload = workspace ? CAN_UPLOAD_ROLES.has(workspace.role) : false;
  const canManage = workspace ? CAN_MANAGE_ROLES.has(workspace.role) : false;
  const documentContent = selectedDocument
    ? buildDocumentContent(selectedDocument)
    : null;

  return (
    <div className="grid gap-6">
      <section className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
              Documents
            </p>
            <h1 className="text-3xl font-semibold text-foreground">
              Workspace document control panel
            </h1>
            <p className="text-sm leading-7 text-slate-700">
              Upload PDFs or plain text files, inspect metadata, and manage
              document status inside the active workspace.
            </p>
          </div>

          <div className="flex gap-3">
            <Link
              className="inline-flex items-center justify-center rounded-full border border-border bg-white px-5 py-3 text-sm font-semibold text-foreground transition hover:bg-slate-50"
              href="/app"
            >
              Back to shell
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1.1fr]">
        <form
          className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]"
          onSubmit={(event) => void handleUpload(event)}
        >
          <div className="space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-800">
              Upload
            </p>
            <p className="text-sm leading-7 text-slate-700">
              Active workspace:{" "}
              <span className="font-semibold text-foreground">
                {workspace?.workspace.name}
              </span>{" "}
              ({workspace?.role})
            </p>
          </div>

          <div className="mt-6 space-y-4">
            <label className="block space-y-2">
              <span className="text-sm font-medium text-foreground">Title</span>
              <input
                className="w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Refund policy"
                required
                value={title}
              />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-foreground">
                Description
              </span>
              <textarea
                className="min-h-28 w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Short note about this document"
                value={description}
              />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-foreground">
                Visibility
              </span>
              <select
                className="w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
                onChange={(event) =>
                  setVisibility(event.target.value as DocumentVisibility)
                }
                value={visibility}
              >
                <option value="workspace">Workspace</option>
                <option value="restricted">Restricted</option>
                <option value="private">Private</option>
              </select>
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-foreground">File</span>
              <input
                accept=".pdf,.txt,text/plain,application/pdf"
                className="w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition file:mr-4 file:rounded-full file:border-0 file:bg-accent file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                required
                type="file"
              />
            </label>
          </div>

          {error ? (
            <p className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </p>
          ) : null}

          <button
            className="mt-6 inline-flex w-full items-center justify-center rounded-full bg-accent px-6 py-3 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-70"
            disabled={!canUpload || submitting}
            type="submit"
          >
            {submitting
              ? "Uploading..."
              : canUpload
                ? "Upload document"
                : "Your role cannot upload"}
          </button>
        </form>

        <div className="rounded-[1.75rem] border border-border bg-[#13212f] p-6 text-slate-100 shadow-[0_16px_60px_rgba(19,33,47,0.12)]">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-200">
              Workspace documents
            </p>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-slate-200">
              {documents.length} total
            </span>
          </div>

          <div className="mt-6 space-y-3">
            {documents.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/20 bg-white/5 px-4 py-6 text-sm text-slate-300">
                No documents yet. Upload the first file for this workspace.
              </div>
            ) : (
              documents.map((document) => (
                <button
                  key={document.id}
                  className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-left transition hover:bg-white/10"
                  onClick={() => void openDocument(document.id)}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-white">
                        {document.title}
                      </p>
                      <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                        {document.status} · {document.visibility} ·{" "}
                        {document.latest_version?.extraction_status ?? "pending"}
                      </p>
                    </div>
                    <span className="text-xs text-slate-400">
                      v{document.latest_version?.version_number ?? 0}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </section>

      {selectedDocument ? (
        <section className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
                Document detail
              </p>
              <h2 className="text-2xl font-semibold text-foreground">
                {selectedDocument.title}
              </h2>
              <p className="text-sm leading-7 text-slate-700">
                {selectedDocument.description || "No description provided."}
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              {canManage ? (
                <>
                  {selectedDocument.status === "failed" ? (
                    <button
                      className="inline-flex items-center justify-center rounded-full border border-border bg-[#0f766e] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#115e59]"
                      onClick={() => void retryDocument(selectedDocument.id)}
                      type="button"
                    >
                      Retry ingestion
                    </button>
                  ) : null}
                  <button
                    className="inline-flex items-center justify-center rounded-full border border-border bg-white px-5 py-3 text-sm font-semibold text-foreground transition hover:bg-slate-50"
                    onClick={() => void disableDocument(selectedDocument.id)}
                    type="button"
                  >
                    Disable document
                  </button>
                  <button
                    className="inline-flex items-center justify-center rounded-full bg-[#9a3412] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#7c2d12]"
                    onClick={() => void deleteDocument(selectedDocument.id)}
                    type="button"
                  >
                    Delete document
                  </button>
                </>
              ) : null}
            </div>
          </div>

          <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {[
              ["Status", selectedDocument.status],
              ["Visibility", selectedDocument.visibility],
              ["Versions", String(selectedDocument.versions.length)],
              [
                "Latest file",
                selectedDocument.latest_version?.file_name ?? "Unavailable",
              ],
              [
                "Chunks",
                String(selectedDocument.latest_version_chunk_count),
              ],
              [
                "Embeddings",
                String(selectedDocument.latest_version_embedding_count),
              ],
              [
                "Logs",
                String(selectedDocument.latest_version_logs.length),
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
              Version history
            </p>
            <div className="mt-4 space-y-3">
              {selectedDocument.versions.map((version) => (
                <div
                  key={version.id}
                  className="flex flex-col gap-1 rounded-2xl border border-border px-4 py-3 text-sm text-slate-700 md:flex-row md:items-center md:justify-between"
                >
                  <span className="font-semibold text-foreground">
                    v{version.version_number} · {version.file_name}
                  </span>
                  <span>
                    {version.mime_type} · {version.file_size_bytes} bytes ·{" "}
                    {version.extraction_status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="grid gap-6">
              <div className="rounded-2xl border border-border bg-white/80 px-4 py-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-foreground">
                      Document content
                    </p>
                    <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      Extracted reading view for the latest version
                    </p>
                  </div>
                  <span className="text-xs uppercase tracking-[0.18em] text-slate-500">
                    {selectedDocument.latest_version?.file_name ?? "latest version"}
                  </span>
                </div>
                <div className="mt-4">
                  {documentContent ? (
                    <div className="max-h-[34rem] overflow-y-auto rounded-2xl border border-border bg-slate-50 px-5 py-5">
                      <pre className="whitespace-pre-wrap text-sm leading-7 text-slate-700">
                        {documentContent}
                      </pre>
                    </div>
                  ) : (
                    <p className="rounded-2xl border border-dashed border-border px-4 py-4 text-sm text-slate-600">
                      The latest version does not have extracted text available
                      yet.
                    </p>
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-white/80 px-4 py-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-foreground">
                    Chunk preview
                  </p>
                  <span className="text-xs uppercase tracking-[0.18em] text-slate-500">
                    {selectedDocument.latest_version_chunk_count} stored
                  </span>
                </div>
                <div className="mt-4 space-y-3">
                  {selectedDocument.latest_version_chunk_preview.length === 0 ? (
                    <p className="rounded-2xl border border-dashed border-border px-4 py-4 text-sm text-slate-600">
                      No chunks are available yet for the latest version.
                    </p>
                  ) : (
                    selectedDocument.latest_version_chunk_preview.map((chunk) => (
                      <ChunkCard chunk={chunk} key={chunk.id} />
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-white/80 px-4 py-4">
              <p className="text-sm font-semibold text-foreground">
                Ingestion logs
              </p>
              <div className="mt-4 space-y-3">
                {selectedDocument.latest_version_logs.length === 0 ? (
                  <p className="rounded-2xl border border-dashed border-border px-4 py-4 text-sm text-slate-600">
                    No ingestion logs recorded yet for the latest version.
                  </p>
                ) : (
                  selectedDocument.latest_version_logs.map((log) => (
                    <LogCard key={log.id} log={log} />
                  ))
                )}
              </div>
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function buildDocumentContent(document: DocumentDetail): string | null {
  const extractedText = document.latest_version_extracted_text?.trim();
  if (extractedText) {
    return extractedText;
  }

  if (document.latest_version_chunk_preview.length === 0) {
    return null;
  }

  return document.latest_version_chunk_preview
    .map((chunk) => chunk.content.trim())
    .filter(Boolean)
    .join("\n\n");
}

function LogCard({ log }: { log: IngestionLogEntry }) {
  const tone =
    log.status === "failed"
      ? "border-red-200 bg-red-50 text-red-800"
      : log.status === "started"
        ? "border-amber-200 bg-amber-50 text-amber-800"
        : "border-emerald-200 bg-emerald-50 text-emerald-800";

  return (
    <div className={`rounded-2xl border px-4 py-4 ${tone}`}>
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold uppercase tracking-[0.16em]">
          {log.step}
        </p>
        <span className="text-xs font-semibold uppercase tracking-[0.16em]">
          {log.status}
        </span>
      </div>
      <p className="mt-2 text-sm leading-6">
        {log.message || "No message provided."}
      </p>
      {log.details ? (
        <pre className="mt-3 overflow-x-auto rounded-2xl bg-white/70 px-3 py-3 text-xs text-slate-700">
          {JSON.stringify(log.details, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}

function ChunkCard({ chunk }: { chunk: DocumentChunkPreview }) {
  return (
    <div className="rounded-2xl border border-border px-4 py-4">
      <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
        <span>Chunk {chunk.chunk_index}</span>
        {chunk.page_number ? <span>Page {chunk.page_number}</span> : null}
        {chunk.section_title ? <span>{chunk.section_title}</span> : null}
      </div>
      <p className="mt-3 text-sm leading-7 text-slate-700">{chunk.content}</p>
      <p className="mt-2 text-xs text-slate-500">
        {chunk.token_count ?? 0} tokens estimated
      </p>
    </div>
  );
}
