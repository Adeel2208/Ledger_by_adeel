import { AXIS_META, cn } from "@/lib/utils";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import type { ComponentType, ReactNode } from "react";

// ── Compact KPI tile ──────────────────────────────────────────────────────────
const TONE: Record<string, string> = {
  brand: "bg-brand-soft text-accent",
  founder: "bg-founder/12 text-founder",
  market: "bg-market/12 text-market",
  idea: "bg-idea/12 text-idea",
  cyan: "bg-cyan/12 text-cyan",
  danger: "bg-danger/12 text-danger",
};

export function KpiTile({
  label,
  value,
  delta,
  icon: Icon,
  tone = "brand",
  gradient,
}: {
  label: string;
  value: ReactNode;
  delta?: ReactNode;
  icon: ComponentType<{ className?: string }>;
  tone?: keyof typeof TONE;
  gradient?: boolean;
}) {
  return (
    <div className="card card-hover p-4">
      <div className="flex items-center justify-between">
        <span className={cn("flex h-8 w-8 items-center justify-center rounded-lg", TONE[tone])}>
          <Icon className="h-4 w-4" />
        </span>
        {delta && <span className="text-[11px] font-semibold text-muted">{delta}</span>}
      </div>
      <div
        className={cn(
          "mt-3 font-display text-2xl font-bold tabular-nums tracking-tight",
          gradient ? "gradient-text" : "text-heading",
        )}
      >
        {value}
      </div>
      <div className="mt-0.5 text-[11px] font-medium uppercase tracking-wide text-faint">{label}</div>
    </div>
  );
}

// ── Pipeline funnel (Sourced → Screened → Scored → Decision) ──────────────────
export function PipelineFunnel({ stages }: { stages: { label: string; count: number }[] }) {
  const max = Math.max(1, ...stages.map((s) => s.count));
  return (
    <div className="space-y-2.5">
      {stages.map((s, i) => {
        const pct = (s.count / max) * 100;
        const conv = i > 0 && stages[i - 1].count > 0
          ? Math.round((s.count / stages[i - 1].count) * 100)
          : null;
        return (
          <div key={s.label} className="flex items-center gap-3">
            <span className="w-20 shrink-0 text-xs font-medium text-muted">{s.label}</span>
            <div className="relative h-7 flex-1 overflow-hidden rounded-lg bg-raised">
              <div
                className="flex h-full items-center rounded-lg bg-brand px-2.5 transition-all duration-700"
                style={{ width: `${Math.max(pct, 9)}%`, opacity: 1 - i * 0.16 }}
              >
                <span className="font-display text-xs font-bold text-white">{s.count}</span>
              </div>
            </div>
            <span className="w-10 shrink-0 text-right text-[11px] tabular-nums text-faint">
              {conv != null ? `${conv}%` : ""}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ── Sourcing mix donut ────────────────────────────────────────────────────────
const PIE_COLORS = ["#6366f1", "#a855f7", "#0891b2", "#10b981"];

export function SourcingDonut({
  data,
  centerLabel,
  centerValue,
}: {
  data: { name: string; value: number }[];
  centerLabel: string;
  centerValue: number;
}) {
  const total = data.reduce((a, b) => a + b.value, 0) || 1;
  return (
    <div className="flex items-center gap-5">
      <div className="relative h-32 w-32 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data.length ? data : [{ name: "none", value: 1 }]}
              dataKey="value"
              innerRadius={44}
              outerRadius={62}
              paddingAngle={2}
              stroke="none"
            >
              {data.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-2xl font-bold text-heading">{centerValue}</span>
          <span className="text-[10px] uppercase tracking-wide text-faint">{centerLabel}</span>
        </div>
      </div>
      <div className="space-y-2">
        {data.map((d, i) => (
          <div key={d.name} className="flex items-center gap-2 text-sm">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
            <span className="capitalize text-muted">{d.name}</span>
            <span className="ml-auto font-semibold tabular-nums text-heading">{d.value}</span>
            <span className="w-9 text-right text-xs text-faint">{Math.round((d.value / total) * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Portfolio-level average axes ──────────────────────────────────────────────
export function PortfolioAxes({ avg }: { avg: Record<"founder" | "market" | "idea", number | null> }) {
  return (
    <div className="space-y-3.5">
      {(["founder", "market", "idea"] as const).map((a) => {
        const meta = AXIS_META[a];
        const v = avg[a] ?? 0;
        return (
          <div key={a}>
            <div className="mb-1.5 flex justify-between text-xs">
              <span className={cn("font-semibold", meta.color)}>{meta.label}</span>
              <span className="font-bold tabular-nums text-heading">{avg[a] != null ? v.toFixed(0) : "—"}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-raised">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${v}%`, background: `linear-gradient(90deg, ${meta.hexLight}, ${meta.hex})` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Compact 3-axis sparkline (for table cells) ────────────────────────────────
export function MiniAxes({
  axes,
}: {
  axes: Partial<Record<"founder" | "market" | "idea", { value: number }>>;
}) {
  const keys = ["founder", "market", "idea"] as const;
  if (!keys.some((k) => axes[k])) return <span className="text-xs text-faint">—</span>;
  return (
    <div className="flex h-8 items-end gap-1" title="Founder / Market / Idea">
      {keys.map((k) => {
        const meta = AXIS_META[k];
        const v = axes[k]?.value ?? 0;
        return (
          <div key={k} className="flex w-2.5 flex-col justify-end" style={{ height: 32 }}>
            <div
              className="w-full rounded-sm"
              style={{ height: `${Math.max(v, 4)}%`, background: meta.hex }}
            />
          </div>
        );
      })}
    </div>
  );
}
