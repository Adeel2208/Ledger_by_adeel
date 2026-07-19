// Response shapes mirroring the backend Experience-layer API.

export type Trend = "improving" | "stable" | "declining";
export type Confidence = "verified" | "corroborated" | "claimed" | "scraped";

export interface AxisMini {
  value: number;
  trend: Trend;
}

export interface Opportunity {
  application_id: number;
  founder_id: number;
  founder_name: string;
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
}

export interface DashboardResponse {
  opportunities: Opportunity[];
  count: number;
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

export interface FounderDetail {
  id: number;
  name: string;
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
