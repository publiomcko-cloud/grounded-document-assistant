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
  ChatAskResponse,
  ConversationDetail,
  ConversationSummary,
  MessageResponse,
} from "@/types/chat";

export function ChatWorkspace() {
  const router = useRouter();
  const [workspace, setWorkspace] = useState<ActiveWorkspaceResponse | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversation, setActiveConversation] =
    useState<ConversationDetail | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

        const loadedConversations = await apiRequest<ConversationSummary[]>(
          "/chat/conversations",
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "X-Workspace-Id": workspaceId,
            },
          },
        );
        setConversations(loadedConversations);
        if (loadedConversations[0]) {
          await openConversation(loadedConversations[0].id, token, workspaceId);
        }
      } catch (requestError) {
        clearStoredAuth();
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Could not load chat workspace.",
        );
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [router]);

  async function openConversation(
    conversationId: string,
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
      const detail = await apiRequest<ConversationDetail>(
        `/chat/conversations/${conversationId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-Id": workspaceId,
          },
        },
      );
      setActiveConversation(detail);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not load the conversation.",
      );
    }
  }

  async function refreshConversations() {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId) {
      return;
    }

    const loaded = await apiRequest<ConversationSummary[]>("/chat/conversations", {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Workspace-Id": workspaceId,
      },
    });
    setConversations(loaded);
  }

  function handleNewChat() {
    setError(null);
    setQuestion("");
    setActiveConversation(null);
  }

  async function handleDeleteConversation(conversationId: string) {
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId) {
      router.replace("/login");
      return;
    }

    const confirmed = window.confirm(
      "Delete this conversation? This action cannot be undone.",
    );
    if (!confirmed) {
      return;
    }

    try {
      setError(null);
      const response = await apiFetch(`/chat/conversations/${conversationId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-Id": workspaceId,
        },
      });
      if (!response.ok) {
        throw new Error("Could not delete the conversation.");
      }

      if (activeConversation?.id === conversationId) {
        setActiveConversation(null);
      }
      await refreshConversations();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not delete the conversation.",
      );
    }
  }

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getStoredToken();
    const workspaceId = getStoredWorkspaceId();
    if (!token || !workspaceId || !question.trim()) {
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const payload = await apiRequest<ChatAskResponse>("/chat/ask", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-Id": workspaceId,
        },
        body: JSON.stringify({
          question,
          conversation_id: activeConversation?.id ?? null,
        }),
      });
      setActiveConversation(payload.conversation);
      setQuestion("");
      await refreshConversations();
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Question failed",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 text-sm text-slate-700 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
        Loading chat workspace...
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <section className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
              Chat
            </p>
            <h1 className="text-3xl font-semibold text-foreground">
              Grounded Q&A with stored citations
            </h1>
            <p className="text-sm leading-7 text-slate-700">
              Ask questions against the active workspace and inspect exactly
              which stored chunks were cited in the answer.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              className="inline-flex items-center justify-center rounded-full bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:bg-accent-strong"
              onClick={handleNewChat}
              type="button"
            >
              New chat
            </button>
            <Link
              className="inline-flex items-center justify-center rounded-full border border-border bg-white px-5 py-3 text-sm font-semibold text-foreground transition hover:bg-slate-50"
              href="/app"
            >
              Back to shell
            </Link>
          </div>
        </div>
        <p className="mt-4 text-sm text-slate-700">
          Active workspace:{" "}
          <span className="font-semibold text-foreground">
            {workspace?.workspace.name}
          </span>
        </p>
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.95fr_1.35fr]">
        <div className="rounded-[1.75rem] border border-border bg-[#13212f] p-6 text-slate-100 shadow-[0_16px_60px_rgba(19,33,47,0.12)]">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-200">
              Conversations
            </p>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-slate-200">
              {conversations.length} total
            </span>
          </div>

          <div className="mt-6 space-y-3">
            {conversations.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/20 bg-white/5 px-4 py-6 text-sm text-slate-300">
                No conversations yet. Ask the first grounded question.
              </div>
            ) : (
              conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`rounded-2xl border px-4 py-4 transition ${
                    activeConversation?.id === conversation.id
                      ? "border-teal-300 bg-white/12"
                      : "border-white/10 bg-white/5 hover:bg-white/10"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <button
                      className="flex-1 text-left"
                      onClick={() => void openConversation(conversation.id)}
                      type="button"
                    >
                      <p className="text-sm font-semibold text-white">
                        {conversation.title || "Untitled conversation"}
                      </p>
                      <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                        {conversation.message_count} messages
                      </p>
                      {conversation.last_message_preview ? (
                        <p className="mt-2 text-sm text-slate-300">
                          {conversation.last_message_preview}
                        </p>
                      ) : null}
                    </button>
                    <button
                      aria-label={`Delete ${conversation.title || "conversation"}`}
                      className="rounded-full border border-white/10 bg-[rgba(255,255,255,0.08)] px-3 py-1 text-xs font-semibold text-white transition hover:bg-[rgba(255,255,255,0.14)]"
                      onClick={() =>
                        void handleDeleteConversation(conversation.id)
                      }
                      type="button"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
                {activeConversation ? "Active conversation" : "New conversation"}
              </p>
              <p className="mt-1 text-sm text-slate-700">
                {activeConversation
                  ? activeConversation.title || "Untitled conversation"
                  : "Your next question will start a fresh thread."}
              </p>
            </div>
            {activeConversation ? (
              <button
                className="inline-flex items-center justify-center rounded-full border border-border bg-white px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-slate-50"
                onClick={handleNewChat}
                type="button"
              >
                Start fresh
              </button>
            ) : null}
          </div>

          <form className="space-y-4" onSubmit={(event) => void handleAsk(event)}>
            <label className="block space-y-2">
              <span className="text-sm font-medium text-foreground">
                Ask a document-grounded question
              </span>
              <textarea
                className="min-h-28 w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="What does the refund policy require?"
                value={question}
              />
            </label>

            {error ? (
              <p className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </p>
            ) : null}

            <button
              className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-3 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-70"
              disabled={submitting}
              type="submit"
            >
              {submitting ? "Generating answer..." : "Ask question"}
            </button>
          </form>

          <div className="mt-8 space-y-4">
            {activeConversation ? (
              activeConversation.messages.map((message) => (
                <MessageCard key={message.id} message={message} />
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-border px-4 py-6 text-sm text-slate-600">
                Start a conversation to see grounded answers and citations here.
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function MessageCard({ message }: { message: MessageResponse }) {
  const isAssistant = message.role === "assistant";
  return (
    <div
      className={`rounded-2xl border px-4 py-4 ${
        isAssistant
          ? "border-border bg-white/90"
          : "border-[#cfd8df] bg-[#edf4f8]"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          {message.role}
        </p>
        {isAssistant && message.model_name ? (
          <span className="text-xs text-slate-500">{message.model_name}</span>
        ) : null}
      </div>
      <p className="mt-3 text-sm leading-7 text-slate-700">{message.content}</p>

      {isAssistant && message.citations.length > 0 ? (
        <div className="mt-4 grid gap-3">
          {message.citations.map((citation) => (
            <div
              key={citation.id}
              className="rounded-2xl border border-border bg-slate-50 px-4 py-4"
            >
              <p className="text-sm font-semibold text-foreground">
                {citation.document_title}
              </p>
              <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                Chunk {citation.chunk_id.slice(0, 8)}
                {citation.page_number ? ` · Page ${citation.page_number}` : ""}
              </p>
              {citation.quote ? (
                <p className="mt-3 text-sm leading-6 text-slate-700">
                  {citation.quote}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
