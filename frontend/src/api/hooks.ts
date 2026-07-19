import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type {
  DashboardResponse,
  FounderDetail,
  Memo,
  Opportunity,
  Thesis,
  Trace,
} from "./types";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch<DashboardResponse>("/dashboard"),
    refetchInterval: 15000,
  });
}

export function useFounder(id: number) {
  return useQuery({
    queryKey: ["founder", id],
    queryFn: () => apiFetch<FounderDetail>(`/founders/${id}`),
    enabled: Number.isFinite(id),
  });
}

export function useMemo(id: number | null) {
  return useQuery({
    queryKey: ["memo", id],
    queryFn: () => apiFetch<Memo>(`/memos/${id}`),
    enabled: id != null,
  });
}

export function useThesis() {
  return useQuery({ queryKey: ["thesis"], queryFn: () => apiFetch<Thesis | null>("/thesis") });
}

export function useTrace(applicationId: number) {
  return useQuery({
    queryKey: ["trace", applicationId],
    queryFn: () => apiFetch<Trace>(`/opportunities/${applicationId}/trace`),
    enabled: Number.isFinite(applicationId),
  });
}

export function useScoreOpportunity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch<Record<string, unknown>>(`/opportunities/${id}/score`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dashboard"] }),
  });
}

export function useScreenOpportunity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch<Record<string, unknown>>(`/opportunities/${id}/screen`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dashboard"] }),
  });
}

export function useGenerateMemo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<Memo>(`/memos/generate/${id}`, { method: "POST" }),
    onSuccess: (memo) => {
      qc.setQueryData(["memo", memo.id], memo);
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateThesis() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<Thesis>) =>
      apiFetch<Thesis>("/thesis", { method: "PUT", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["thesis"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useSearch() {
  return useMutation({
    mutationFn: (query: string) =>
      apiFetch<{ id: string; score: number; metadata: Record<string, unknown> }[]>("/search", {
        method: "POST",
        body: JSON.stringify({ query, k: 10 }),
      }),
  });
}

// ── Inbound apply (C1) ────────────────────────────────────────────────────────
export interface ApplyResult {
  application_id: number;
  founder_id: number;
  founder_name: string;
  signals_extracted: number;
  screening: { decision: string; reason: string; thesis_fit: number };
  warnings: string[];
}

export function useApply() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (form: FormData) =>
      apiFetch<ApplyResult>("/applications", { method: "POST", body: form }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dashboard"] }),
  });
}

// ── Outbound sourcing (D1/D3) ─────────────────────────────────────────────────
export interface Discovered {
  founder_id: number;
  name: string;
  github_handle: string | null;
  is_cold_start: boolean;
  founder_score: number | null;
  momentum: string | null;
  signal_count: number;
}

export function useDiscovered() {
  return useQuery({
    queryKey: ["discovered"],
    queryFn: () => apiFetch<Discovered[]>("/sourcing/discovered"),
  });
}

export function useScan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { source: string; params: Record<string, unknown>; is_cold_start?: boolean }) =>
      apiFetch<Record<string, unknown>>("/sourcing/scan", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["discovered"] }),
  });
}

export function useActivate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ founderId, ...body }: { founderId: number; company_name: string; sector?: string; stage?: string; geography?: string }) =>
      apiFetch<{ application_id: number; screening: { decision: string; reason: string } }>(
        `/sourcing/${founderId}/activate`,
        { method: "POST", body: JSON.stringify(body) },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["discovered"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export type { Opportunity };
