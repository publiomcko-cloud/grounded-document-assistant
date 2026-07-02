const CONFIGURED_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export const API_BASE_URL = CONFIGURED_API_BASE_URL ?? "http://localhost:8000";

function getApiCandidates(): string[] {
  const configured = CONFIGURED_API_BASE_URL ? [CONFIGURED_API_BASE_URL] : [];

  if (typeof window === "undefined") {
    return [...configured, "http://localhost:8000"];
  }

  const hostname = window.location.hostname || "localhost";
  const localFallbacks = [
    `http://${hostname}:8000`,
    `http://${hostname}:8017`,
    `http://localhost:8000`,
    `http://localhost:8017`,
    `http://127.0.0.1:8000`,
    `http://127.0.0.1:8017`,
  ];

  return [...new Set([...configured, ...localFallbacks])];
}

export function getApiUrl(
  path: string,
  baseUrl: string = API_BASE_URL,
): string {
  return `${baseUrl}${path}`;
}

export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const candidates = getApiCandidates();

  let lastNetworkError: Error | null = null;
  for (const baseUrl of candidates) {
    try {
      return await fetch(getApiUrl(path, baseUrl), init);
    } catch (requestError) {
      if (requestError instanceof TypeError) {
        lastNetworkError = requestError;
        continue;
      }

      throw requestError;
    }
  }

  throw new Error(
    lastNetworkError
      ? "Could not reach the API. Make sure the backend is running and try again."
      : "Request failed",
  );
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...(init.headers ?? {}),
  };

  const response = await apiFetch(path, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const message = await response
      .json()
      .then((data) => data.detail ?? "Request failed")
      .catch(() => "Request failed");
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}
