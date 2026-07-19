import type { OptimalTiming } from "@/api/types";
import { Card, SectionLabel } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import { CircleHelp, Clock, TrendingUp, XCircle } from "lucide-react";

/** Turn the backend's recommendation slug into presentation. */
function present(rec: string) {
  if (rec === "invest_now")
    return { label: "Invest now", icon: TrendingUp, cls: "text-success", band: "bg-success" };
  if (rec === "insufficient_data")
    return { label: "Insufficient data", icon: CircleHelp, cls: "text-muted", band: "bg-faint" };
  if (rec === "pass")
    return { label: "Pass", icon: XCircle, cls: "text-danger", band: "bg-danger" };
  const m = rec.match(/^wait_(\d+)_months?$/);
  if (m) return { label: `Wait ${m[1]} months`, icon: Clock, cls: "text-idea", band: "bg-idea" };
  return { label: rec.replace(/_/g, " "), icon: CircleHelp, cls: "text-muted", band: "bg-faint" };
}

/**
 * The headline verdict — a hero number, not a chart.
 *
 * One decision with its reasoning is the single most important thing on the
 * page, so it gets size and position rather than being buried in a grid.
 */
export function TimingVerdict({ t }: { t: OptimalTiming }) {
  const v = present(t.recommendation);
  const Icon = v.icon;
  const showUrgency = t.recommendation !== "insufficient_data";

  return (
    <Card className="overflow-hidden">
      <div className={cn("h-1", v.band)} />
      <div className="p-5">
        <SectionLabel>Timing recommendation</SectionLabel>

        <div className="mt-3 flex items-start gap-4">
          <Icon className={cn("mt-1 h-9 w-9 shrink-0", v.cls)} />
          <div className="min-w-0 flex-1">
            <div className={cn("font-display text-2xl font-semibold", v.cls)}>{v.label}</div>
            <ul className="mt-2 space-y-1">
              {t.reasoning.map((r, i) => (
                <li key={i} className="text-xs leading-relaxed text-muted">
                  {r}
                </li>
              ))}
            </ul>
          </div>

          {showUrgency && (
            <div className="shrink-0 text-right">
              <div className="text-[11px] uppercase tracking-wide text-faint">Urgency</div>
              <div className="font-display text-2xl font-semibold tabular-nums text-heading">
                {Math.round(t.urgency_score * 100)}
              </div>
              {t.window_closing_in_months != null && (
                <div className="text-[11px] text-faint">window ~{t.window_closing_in_months}mo</div>
              )}
            </div>
          )}
        </div>

        {t.expected_milestones.length > 0 && (
          <div className="mt-4 border-t border-border pt-3">
            <div className="mb-1.5 text-[11px] uppercase tracking-wide text-faint">
              Expected by then
            </div>
            <div className="flex flex-wrap gap-2">
              {t.expected_milestones.map((m, i) => (
                <span key={i} className="rounded-md bg-raised px-2 py-1 text-xs text-muted">
                  {m}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
