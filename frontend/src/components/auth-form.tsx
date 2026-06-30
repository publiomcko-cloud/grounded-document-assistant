"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { apiRequest } from "@/lib/api";
import { setStoredToken } from "@/lib/auth-storage";
import { TokenResponse } from "@/types/auth";

type AuthFormProps = {
  mode: "login" | "register";
};

const demoCredentials = {
  ownerEmail: "owner@example.com",
  viewerEmail: "viewer@example.com",
  password: "grounded-demo",
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isRegister = mode === "register";

  function fillDemoCredentials(role: "owner" | "viewer") {
    setEmail(
      role === "owner"
        ? demoCredentials.ownerEmail
        : demoCredentials.viewerEmail,
    );
    setPassword(demoCredentials.password);
    setError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegister) {
        await apiRequest("/auth/register", {
          method: "POST",
          body: JSON.stringify({ name, email, password }),
        });
      }

      const token = await apiRequest<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      setStoredToken(token.access_token);
      router.push("/app");
      router.refresh();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Authentication failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <form
        className="rounded-[1.75rem] border border-border bg-surface-strong p-6 shadow-[0_16px_60px_rgba(19,33,47,0.1)]"
        onSubmit={handleSubmit}
      >
        <div className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm">
            {isRegister ? "Create account" : "Sign in"}
          </p>
          <h1 className="text-3xl font-semibold text-foreground">
            {isRegister
              ? "Start your workspace foundation."
              : "Access your grounded workspace."}
          </h1>
          <p className="text-sm leading-7 text-slate-700">
            {isRegister
              ? "Registration creates your first workspace and owner membership automatically."
              : "Use the seeded demo account or sign in with a registered user."}
          </p>
        </div>

        <div className="mt-8 space-y-4">
          {isRegister ? (
            <label className="block space-y-2">
              <span className="text-sm font-medium text-foreground">Name</span>
              <input
                className="w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
                onChange={(event) => setName(event.target.value)}
                placeholder="Jane Doe"
                required
                value={name}
              />
            </label>
          ) : null}

          <label className="block space-y-2">
            <span className="text-sm font-medium text-foreground">Email</span>
            <input
              className="w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="owner@example.com"
              required
              type="email"
              value={email}
            />
          </label>

          <label className="block space-y-2">
            <span className="text-sm font-medium text-foreground">
              Password
            </span>
            <input
              className="w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm outline-none transition focus:border-accent"
              minLength={8}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
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
          disabled={loading}
          type="submit"
        >
          {loading
            ? "Working..."
            : isRegister
              ? "Create account and sign in"
              : "Sign in"}
        </button>

        <p className="mt-4 text-sm text-slate-700">
          {isRegister ? "Already have an account?" : "Need a new account?"}{" "}
          <Link
            className="font-semibold text-accent-strong underline-offset-4 hover:underline"
            href={isRegister ? "/login" : "/register"}
          >
            {isRegister ? "Go to login" : "Register"}
          </Link>
        </p>
      </form>

      <aside className="rounded-[1.75rem] border border-border bg-[#13212f] p-6 text-slate-100 shadow-[0_16px_60px_rgba(19,33,47,0.12)]">
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-teal-200">
          Demo credentials
        </p>
        <div className="mt-6 space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-white">Owner</p>
              {!isRegister ? (
                <button
                  className="inline-flex items-center justify-center rounded-full border border-white/10 bg-[rgba(255,255,255,0.08)] px-3 py-1 text-xs font-semibold text-white transition hover:bg-[rgba(255,255,255,0.14)]"
                  onClick={() => fillDemoCredentials("owner")}
                  type="button"
                >
                  Use owner demo
                </button>
              ) : null}
            </div>
            <p className="mt-2 text-sm text-slate-300">
              {demoCredentials.ownerEmail}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-white">Viewer</p>
              {!isRegister ? (
                <button
                  className="inline-flex items-center justify-center rounded-full border border-white/10 bg-[rgba(255,255,255,0.08)] px-3 py-1 text-xs font-semibold text-white transition hover:bg-[rgba(255,255,255,0.14)]"
                  onClick={() => fillDemoCredentials("viewer")}
                  type="button"
                >
                  Use viewer demo
                </button>
              ) : null}
            </div>
            <p className="mt-2 text-sm text-slate-300">
              {demoCredentials.viewerEmail}
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
            <p className="text-sm font-semibold text-white">Password</p>
            <p className="mt-2 text-sm text-slate-300">
              {demoCredentials.password}
            </p>
          </div>
          {!isRegister ? (
            <p className="text-sm leading-6 text-slate-300">
              Click one of the demo buttons to fill both the email and password
              fields automatically.
            </p>
          ) : null}
        </div>
      </aside>
    </div>
  );
}
