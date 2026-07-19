// Typed fetch wrapper around the backend Experience-layer API.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  // FormData must set its own multipart boundary — don't force JSON headers on it.
  const isForm = init?.body instanceof FormData;
  const headers = isForm
    ? (init?.headers ?? {})
    : { "Content-Type": "application/json", ...(init?.headers ?? {}) };
  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${detail ? ` — ${detail.slice(0, 200)}` : ""}`);
  }
  return res.json() as Promise<T>;
}
