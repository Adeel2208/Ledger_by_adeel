// Response shapes mirroring the backend Experience-layer API.

export type Trend = "improving" | "stable" | "declining";
export type Confidence = "verified" | "corroborated" | "claimed" | "scraped";

export interface AxisMini {
  value: number;
  trend: Trend;
}

/** Compact avatar payload — the subset of the profile a table row needs. */
export interface AvatarBlock {
  photo_url: string | null;
  monogram: { initials: string; color: string };
}

export interface Opportunity {
  application_id: number;
  founder_id: number;
  founder_name: string;
  avatar: AvatarBlock;
  company_name: string;
  sector: string | null;
  stage: string | null;
  geography: string | null;
  channel: string;
  is_cold_start: boolean;
  screening_decision: string | null;
  thesis_fit: number;
  founder_score: number | null;
  momentum: Trend | null;
  axes: Partial<Record<"founder" | "market" | "idea", AxisMini>>;
  has_memo: boolean;
  memo_id: number | null;
  recommendation: string | null;
  trust_score: number | null;
  /** Hours from first ingested signal to the memo decision; null if undecided. */
  decision_hours: number | null;
}

export interface DashboardResponse {
  opportunities: Opportunity[];
  count: number;
  /** Fund-level speed instrumentation: first signal → decision. */
  velocity: {
    decided_count: number;
    median_hours_to_decision: number | null;
    within_24h_rate: number | null;
  };
}

export interface Signal {
  id: number;
  source: string;
  record_type: string;
  confidence: Confidence;
  external_url: string | null;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface ScorePoint {
  value: number;
  momentum: Trend;
  computed_at: string;
}

export interface WorkHistoryEntry {
  company: string | null;
  title: string | null;
  start: string | null;
  end: string | null;
  summary: string | null;
}

/** Founder-supplied profile. Every field is optional: absence is a disclosed
 *  gap, and `monogram` always provides a designed avatar fallback. */
export interface FounderProfile {
  photo_url: string | null;
  monogram: { initials: string; color: string };
  headline: string | null;
  bio: string | null;
  role: string | null;
  location: string | null;
  personal_url: string | null;
  twitter_handle: string | null;
  linkedin_url: string | null;
  work_history: WorkHistoryEntry[];
  profile_updated_at: string | null;
  completeness: { present: string[]; missing: string[]; pct: number };
}

export interface FounderDetail {
  id: number;
  name: string;
  profile: FounderProfile;
  email: string | null;
  github_handle: string | null;
  linkedin_url: string | null;
  is_cold_start: boolean;
  founder_score: number | null;
  momentum: Trend | null;
  components: Record<string, number>;
  score_history: ScorePoint[];
  signals: Signal[];
  data_quality: {
    signal_count: number;
    freshness: Record<string, { last_seen: string; age_days: number }>;
    reliability_mix: Record<string, number>;
    covered: string[];
    gaps: string[];
  };
}

export interface AxisScore {
  value: number;
  trend: Trend;
  rationale: string;
  evidence_ids: number[];
  scored_at?: string;
}

export interface Evidence {
  signal_id: number;
  confidence: Confidence;
  source: string | null;
  external_url: string | null;
}

export interface MemoClaim {
  text: string;
  confidence: Confidence;
  contradicted: boolean;
  evidence: Evidence[];
}

export interface MemoSection {
  title: string;
  body: string;
  is_gap: boolean;
  claims: MemoClaim[];
}

export interface Memo {
  id: number;
  application_id: number;
  recommendation: string | null;
  trust_score: number | null;
  sections: MemoSection[];
}

export interface Artifact {
  signal_id: number;
  source: string;
  record_type: string;
  confidence: Confidence;
  excerpt: string;
  external_url: string | null;
  timestamp: string | null;
}

export interface TraceStep {
  stage: string;
  title: string;
  conclusion: string;
  rationale: string;
  evidence: (Artifact | null)[];
  pool: number;
  axis?: string;
  memo_id?: number;
}

export interface Trace {
  application_id: number;
  founder_id: number;
  founder_name: string;
  company_name: string;
  channel: string;
  is_cold_start: boolean;
  signal_pool: number;
  steps: TraceStep[];
}

export interface Thesis {
  id: number;
  sectors: string[];
  stages: string[];
  geographies: string[];
  check_size_min: number | null;
  check_size_max: number | null;
  ownership_target: number | null;
  risk_appetite: string;
}

// ── Intelligence layer (signal correlation, prediction, risk, anomalies) ──────

export interface MomentumIndicator {
  dimension: string;
  direction: string;
  velocity: number;
  timespan_days: number;
  confidence: number;
}

export interface QualitySignal {
  indicator: string;
  score: number;
  evidence: string;
  weight: number;
}

export interface SignalContradiction {
  metric: string;
  severity: string;
  explanation: string;
  sources: string[];
  values: unknown[];
}

export interface SignalAnalysis {
  founder_id: number;
  consistency_score: number;
  confidence: number;
  analyzed_signal_count: number;
  contradictions: SignalContradiction[];
  momentum_indicators: MomentumIndicator[];
  quality_signals: QualitySignal[];
  network_effects: { effect_type: string; strength: number; evidence: string }[];
  red_flags: string[];
  green_flags: string[];
  generated_at: string;
}

export interface SuccessProbability {
  founder_id: number;
  confidence: number;
  probabilities: {
    product_market_fit: number;
    series_a_funding: number;
    profitability: number;
    exit_potential: number;
  };
  key_drivers: string[];
  risk_factors: string[];
  timing_estimates: { months_to_pmf: number | null; months_to_funding: number | null };
}

/** `risk_level` is "unknown" when there are no signals — an undetermined state,
 *  explicitly not a low or high risk finding. */
export interface RiskAssessment {
  founder_id: number;
  overall_risk: number;
  risk_level: "low" | "medium" | "high" | "critical" | "unknown";
  risk_dimensions: {
    execution: number;
    market_timing: number;
    team: number;
    competitive: number;
    financial: number;
  };
  risk_factors: { category: string; severity: string; description: string }[];
  mitigation_suggestions: string[];
}

/** `recommendation` is "insufficient_data" when evidence is too thin to time. */
export interface OptimalTiming {
  founder_id: number;
  recommendation: string;
  reasoning: string[];
  wait_months: number | null;
  expected_milestones: string[];
  window_closing_in_months: number | null;
  urgency_score: number;
}

export interface AnomalyReport {
  founder_id: number;
  overall_risk_level: string;
  recommended_action: string;
  anomaly_count: number;
  statistical_anomalies: { description?: string; metric?: string; severity?: string }[];
  behavioral_anomalies: { description?: string; metric?: string; severity?: string }[];
  temporal_anomalies: { description?: string; metric?: string; severity?: string }[];
}

/** Everything the Intelligence page needs, fetched in parallel. */
export interface FounderIntelligence {
  analysis: SignalAnalysis;
  success: SuccessProbability;
  risk: RiskAssessment;
  timing: OptimalTiming;
  anomalies: AnomalyReport;
}

// ── Natural-language multi-attribute search (FR-3) ────────────────────────────

/** How the parser read the query — shown to the user so the interpretation is
 *  inspectable, not a black box. Mirrors StructuredQuery on the backend. */
export interface ParsedQuery {
  entities: {
    sectors: string[];
    locations: string[];
    technologies: string[];
    accelerators: string[];
    companies: string[];
    investors: string[];
  };
  attributes: Record<string, boolean | null>;
  ranges: Record<string, number | null>;
  temporal: { period: string | null; founded_after: string | null; founded_before: string | null };
  semantic_query: string;
  negations: string[];
  confidence: number;
}

export interface SearchResult {
  founder_id: number;
  founder_name: string;
  company_id: number | null;
  company_name: string | null;
  relevance_score: number;
  match_reasons: string[];
  highlights: Record<string, string>;
  avatar?: AvatarBlock;
}

export interface SearchResponse {
  query: string;
  parsed: ParsedQuery;
  results: SearchResult[];
  total: number;
}
