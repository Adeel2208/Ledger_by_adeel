// Shared domain types — mirror the backend Pydantic schemas.

export type Trend = "improving" | "stable" | "declining";
export type Axis = "founder" | "market" | "idea";

export interface AxisScore {
  axis: Axis;
  value: number;
  trend: Trend;
  rationale: string;
  evidenceIds: number[];
}

// The three axes travel together but are NEVER collapsed into one number.
export interface TripleScore {
  founder: AxisScore;
  market: AxisScore;
  idea: AxisScore;
}

export interface Founder {
  id: number;
  name: string;
  isColdStart: boolean;
  founderScore: number | null;
  momentum: Trend | null;
}

export type Confidence = "verified" | "corroborated" | "claimed";

export interface Claim {
  id: number;
  text: string;
  confidence: Confidence;
  contradicted: boolean;
  evidenceIds: number[];
}
