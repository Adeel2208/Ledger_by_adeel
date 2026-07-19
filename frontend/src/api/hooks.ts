import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type {
  AnomalyReport,
  DashboardResponse,
  FounderDetail,
  FounderIntelligence,
  Memo,
  Opportunity,
  OptimalTiming,
  RiskAssessment,
  SearchResponse,
  SignalAnalysis,
  SuccessProbability,
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

export interface ChannelStats {
  channel: string;
  count: number;
  avg_thesis_fit: number | null;
  avg_founder_score: number | null;
  pass_rate: number;
  avg_axes: Record<string, number | null>;
}
export interface ChannelAnalytics {
  by_channel: ChannelStats[];
  by_source: { source: string; founders: number }[];
  underexplored: string[];
  suggestion: string | null;
}

export function useChannelAnalytics() {
  return useQuery({
    queryKey: ["analytics", "channels"],
    queryFn: () => apiFetch<ChannelAnalytics>("/analytics/channels"),
    refetchInterval: 20000,
  });
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

/** Multi-attribute NL search (FR-3). The response carries the parser's reading
 *  of the query so the UI can show *how* the system understood it. */
export function useSearch() {
  return useMutation({
    mutationFn: (query: string) =>
      apiFetch<SearchResponse>("/search", {
        method: "POST",
        body: JSON.stringify({ query, k: 25 }),
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
      apiFetch<{
        application_id: number;
        screening: { decision: string; reason: string };
        /** LLM-drafted cold-outreach message grounded in observed signals;
         *  null when the founder has no signals to ground it in. */
        outreach_draft: string | null;
      }>(`/sourcing/${founderId}/activate`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["discovered"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export type { Opportunity };

// ── Intelligence (C4) ─────────────────────────────────────────────────────────

/**
 * Full intelligence package for one founder.
 *
 * The backend exposes each analysis as its own endpoint and a
 * `/complete-intelligence` roll-up, but that roll-up drops the risk dimensions
 * and momentum detail these views chart — so fetch the five in parallel
 * instead. One React Query key still gives the page a single loading state.
 */
export function useFounderIntelligence(founderId: number) {
  return useQuery({
    queryKey: ["intelligence", founderId],
    enabled: Number.isFinite(founderId),
    // Each call re-runs the engines server-side; don't refetch on every focus.
    staleTime: 60_000,
    queryFn: async (): Promise<FounderIntelligence> => {
      const body = JSON.stringify({ founder_id: founderId });
      const post = <T,>(p: string) => apiFetch<T>(p, { method: "POST", body });
      const [analysis, success, risk, timing, anomalies] = await Promise.all([
        post<SignalAnalysis>("/intelligence/analyze"),
        post<SuccessProbability>("/intelligence/success-probability"),
        post<RiskAssessment>("/intelligence/risk-assessment"),
        post<OptimalTiming>("/intelligence/optimal-timing"),
        post<AnomalyReport>("/intelligence/anomaly-detection"),
      ]);
      return { analysis, success, risk, timing, anomalies };
    },
  });
}

export interface PatternReport {
  analyzed_applications: number;
  success_patterns: { pattern: string; confidence: number; frequency: number; indicators: string[] }[];
  failure_modes: { mode: string; frequency: number; indicators: string[] }[];
}

export function usePatterns() {
  return useQuery({
    queryKey: ["patterns"],
    staleTime: 300_000,
    queryFn: () =>
      apiFetch<PatternReport>("/intelligence/mine-patterns", {
        method: "POST",
        body: JSON.stringify({ lookback_months: 24, min_confidence: 0.6 }),
      }),
  });
}
