import { cn, AXIS_META, CONFIDENCE_META } from "@/lib/utils";
import type { Confidence, Trend } from "@/api/types";
import { ArrowDownRight, ArrowRight, ArrowUpRight, AlertTriangle } from "lucide-react";

export function TrendArrow({ trend, className }: { trend?: Trend; className?: string }) {
  if (trend === "improving")
    return <ArrowUpRight className={cn("h-4 w-4 text-success", className)} />;
  if (trend === "declining")
    return <ArrowDownRight className={cn("h-4 w-4 text-danger", className)} />;
  return <ArrowRight className={cn("h-4 w-4 text-faint", className)} />;
}

/** One axis as a labelled 0-100 bar. The three are always shown side by side, never merged. */
export function AxisBar({
  axis,
  value,
  trend,
}: {
  axis: "founder" | "market" | "idea";
  value?: number;
  trend?: Trend;
}) {
  const meta = AXIS_META[axis];
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className={cn("font-medium", meta.color)}>{meta.label}</span>
        <span className="flex items-center gap-1 tabular-nums text-muted">
          {value != null ? value : "—"}
          {value != null && <TrendArrow trend={trend} className="h-3.5 w-3.5" />}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-raised">
        <div
          className={cn("h-full rounded-full transition-all", meta.bar)}
          style={{ width: `${value ?? 0}%` }}
        />
      </div>
    </div>
  );
}

export function TripleAxis({
  axes,
}: {
  axes: Partial<Record<"founder" | "market" | "idea", { value: number; trend: Trend }>>;
}) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {(["founder", "market", "idea"] as const).map((a) => (
        <AxisBar key={a} axis={a} value={axes[a]?.value} trend={axes[a]?.trend} />
      ))}
    </div>
  );
}

/** Circular Trust Score ring with traffic-light color. */
export function TrustRing({ value, size = 56 }: { value: number | null; size?: number }) {
  const v = value ?? 0;
  const r = size / 2 - 5;
  const c = 2 * Math.PI * r;
  const color = v >= 70 ? "#059669" : v >= 45 ? "#d97706" : "#dc2626";
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e2e8f0" strokeWidth={5} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={5}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c - (c * v) / 100}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold tabular-nums">
        {value == null ? "—" : Math.round(v)}
      </div>
    </div>
  );
}

export function ConfidencePill({ confidence }: { confidence: Confidence }) {
  const meta = CONFIDENCE_META[confidence] ?? CONFIDENCE_META.scraped;
  return <span className={cn("pill", meta.cls)}>{meta.label}</span>;
}

export function ContradictionFlag() {
  return (
    <span className="pill bg-danger/15 text-danger">
      <AlertTriangle className="h-3 w-3" /> Contradicted
    </span>
  );
}
