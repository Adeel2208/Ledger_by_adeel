// Typed fetch wrapper around the backend Experience-layer API.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

/** Origin serving founder media. Photos are mounted at `/media` on the API
 *  host — outside the `/api/v1` prefix — so strip the path off the base URL. */
export const MEDIA_BASE = BASE_URL.replace(/\/api\/v\d+\/?$/, "");

/** Resolve a backend-relative media path to an absolute URL. */
export function mediaUrl(path: string | null): string | null {
  if (!path) return null;
  return /^https?:\/\//.test(path) ? path : `${MEDIA_BASE}${path}`;
}

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
