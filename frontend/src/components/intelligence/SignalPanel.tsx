import type { AnomalyReport, SignalAnalysis } from "@/api/types";
import { Card, EmptyState, Pill, SectionLabel } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import { ArrowDownRight, ArrowRight, ArrowUpRight, Flag, TriangleAlert } from "lucide-react";

function DirectionArrow({ direction }: { direction: string }) {
  if (direction === "accelerating" || direction === "increasing" || direction === "up")
    return <ArrowUpRight className="h-3.5 w-3.5 text-success" />;
  if (direction === "declining" || direction === "decreasing" || direction === "down")
    return <ArrowDownRight className="h-3.5 w-3.5 text-danger" />;
  return <ArrowRight className="h-3.5 w-3.5 text-faint" />;
}

/** Green/red flags — the fastest read on a founder, so they lead the panel. */
export function FlagsPanel({ a }: { a: SignalAnalysis }) {
  const none = a.green_flags.length === 0 && a.red_flags.length === 0;

  return (
    <Card className="p-5">
      <div className="flex items-baseline justify-between">
        <SectionLabel>Flags</SectionLabel>
        <span className="text-[11px] text-faint">{a.analyzed_signal_count} signals analysed</span>
      </div>

      {none ? (
        <div className="mt-2">
          <EmptyState compact title="No flags raised" hint="Nothing stood out either way in the signals." />
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          {a.green_flags.length > 0 && (
            <div>
              <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-success">
                <Flag className="h-3.5 w-3.5" /> Green flags
              </div>
              <ul className="space-y-1.5">
                {a.green_flags.map((f, i) => (
                  <li key={i} className="rounded-md bg-success/8 px-2.5 py-1.5 text-xs text-ink">
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {a.red_flags.length > 0 && (
            <div>
              <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-danger">
                <TriangleAlert className="h-3.5 w-3.5" /> Red flags
              </div>
              <ul className="space-y-1.5">
                {a.red_flags.map((f, i) => (
                  <li key={i} className="rounded-md bg-danger/8 px-2.5 py-1.5 text-xs text-ink">
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

/** Momentum per dimension — direction plus how fast, with an arrow so the
 *  state is never conveyed by colour alone. */
export function MomentumPanel({ a }: { a: SignalAnalysis }) {
  return (
    <Card className="p-5">
      <SectionLabel>Momentum</SectionLabel>
      {a.momentum_indicators.length === 0 ? (
        <div className="mt-2">
          <EmptyState
            compact
            title="No momentum detected"
            hint="Needs repeated observations of the same dimension over time."
          />
        </div>
      ) : (
        <ul className="mt-4 space-y-2.5">
          {a.momentum_indicators.map((m, i) => (
            <li key={i} className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-2">
                <DirectionArrow direction={m.direction} />
                <span className="truncate text-sm text-ink">{m.dimension.replace(/_/g, " ")}</span>
              </div>
              <div className="flex shrink-0 items-center gap-2 text-xs">
                <span className="text-muted">{m.direction}</span>
                <span className="tabular-nums text-faint">over {m.timespan_days}d</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

/** Collapse identical findings into one row with a count.
 *
 *  The detectors emit one entry per offending signal, so a founder with a dozen
 *  same-day signals yields a dozen byte-identical "temporal inconsistency"
 *  rows. Listing them all buries the distinct findings underneath; "×11" says
 *  the same thing in one line without losing the magnitude. */
function dedupe(items: { description?: string; metric?: string; severity?: string }[]) {
  const seen = new Map<string, { text: string; severity?: string; count: number }>();
  for (const it of items) {
    const text = it.description ?? it.metric ?? "anomaly";
    const key = `${text}|${it.severity ?? ""}`;
    const hit = seen.get(key);
    if (hit) hit.count += 1;
    else seen.set(key, { text, severity: it.severity, count: 1 });
  }
  return [...seen.values()];
}

/** Anomalies across statistical / behavioural / temporal detectors. */
export function AnomalyPanel({ r }: { r: AnomalyReport }) {
  const groups = [
    { label: "Statistical", items: dedupe(r.statistical_anomalies) },
    { label: "Behavioural", items: dedupe(r.behavioral_anomalies) },
    { label: "Temporal", items: dedupe(r.temporal_anomalies) },
  ].filter((g) => g.items.length > 0);

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <SectionLabel>Anomaly detection</SectionLabel>
        <Pill
          className={cn(
            r.anomaly_count === 0 ? "bg-raised text-muted" : "bg-danger/12 text-danger",
          )}
        >
          {r.anomaly_count} found
        </Pill>
      </div>

      {groups.length === 0 ? (
        <p className="mt-3 text-xs text-muted">
          No anomalies detected.{" "}
          <span className="text-faint">
            Recommended action: {r.recommended_action.replace(/_/g, " ")}.
          </span>
        </p>
      ) : (
        <div className="mt-4 space-y-3">
          {groups.map((g) => (
            <div key={g.label}>
              <div className="mb-1.5 text-[11px] uppercase tracking-wide text-faint">{g.label}</div>
              <ul className="space-y-1">
                {g.items.map((it, i) => (
                  <li key={i} className="text-xs leading-relaxed text-muted">
                    · {it.text}
                    {it.count > 1 && (
                      <span className="ml-1 tabular-nums text-heading">×{it.count}</span>
                    )}
                    {it.severity && <span className="ml-1 text-faint">({it.severity})</span>}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
