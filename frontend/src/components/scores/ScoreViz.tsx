import { AXIS_META, CONFIDENCE_META, cn } from "@/lib/utils";
import type { Confidence, Trend } from "@/api/types";
import { AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";

export function TrendArrow({ trend, className }: { trend?: Trend; className?: string }) {
  if (trend === "improving")
    return <ArrowUpRight className={cn("h-4 w-4 text-success", className)} strokeWidth={2.4} />;
  if (trend === "declining")
    return <ArrowDownRight className={cn("h-4 w-4 text-danger", className)} strokeWidth={2.4} />;
  return <ArrowRight className={cn("h-4 w-4 text-faint", className)} strokeWidth={2.4} />;
}

/** One axis as a labelled 0-100 gradient bar. The three are always shown side by side. */
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
      <div className="mb-1.5 flex items-center justify-between text-xs">
        <span className={cn("font-semibold", meta.color)}>{meta.label}</span>
        <span className="flex items-center gap-1 font-semibold tabular-nums text-heading">
          {value != null ? value : "—"}
          {value != null && <TrendArrow trend={trend} className="h-3.5 w-3.5" />}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-raised">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${value ?? 0}%`,
            background: `linear-gradient(90deg, ${meta.hexLight}, ${meta.hex})`,
          }}
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
    <div className="grid grid-cols-3 gap-3.5">
      {(["founder", "market", "idea"] as const).map((a) => (
        <AxisBar key={a} axis={a} value={axes[a]?.value} trend={axes[a]?.trend} />
      ))}
    </div>
  );
}

/** Circular Trust Score ring with a gradient stroke + soft glow. */
export function TrustRing({ value, size = 56 }: { value: number | null; size?: number }) {
  const v = value ?? 0;
  const r = size / 2 - 5;
  const c = 2 * Math.PI * r;
  const id = `trust-${size}`;
  const stops =
    v >= 70
      ? ["#34d399", "#10b981"]
      : v >= 45
        ? ["#fbbf24", "#f59e0b"]
        : ["#f87171", "#ef4444"];
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={stops[0]} />
            <stop offset="100%" stopColor={stops[1]} />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#eae8f4" strokeWidth={5} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={`url(#${id})`}
          strokeWidth={5}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c - (c * v) / 100}
          style={{ transition: "stroke-dashoffset 0.6s cubic-bezier(0.16,1,0.3,1)" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center font-display text-sm font-bold tabular-nums text-heading">
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
    <span className="pill bg-danger/12 text-danger ring-1 ring-danger/20">
      <AlertTriangle className="h-3 w-3" /> Contradicted
    </span>
  );
}
