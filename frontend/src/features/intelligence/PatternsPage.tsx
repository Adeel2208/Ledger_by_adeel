import { usePatterns } from "@/api/hooks";
import { Card, EmptyState, SectionLabel, Spinner, StatTile } from "@/components/ui/primitives";
import { Layers, TrendingDown, TrendingUp } from "lucide-react";

/**
 * Fund-wide patterns mined from past decisions.
 *
 * This is the only view that looks across the whole portfolio of *decisions*
 * rather than one founder — it answers "what has actually predicted outcomes
 * for us", which is the thing a partner meeting argues about.
 */
export default function PatternsPage() {
  const { data, isLoading } = usePatterns();

  if (isLoading)
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-6 w-6 text-accent" />
      </div>
    );

  if (!data) return null;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="flex items-center gap-2 font-display text-xl font-semibold text-heading">
          <Layers className="h-5 w-5 text-accent" /> Patterns
        </h1>
        <p className="mt-0.5 text-sm text-muted">
          What has actually predicted outcomes across your decisions — mined, not assumed.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile
          label="Applications analysed"
          value={data.analyzed_applications}
          icon={Layers}
          tone="brand"
          gradient
        />
        <StatTile
          label="Success patterns"
          value={data.success_patterns.length}
          icon={TrendingUp}
          tone="market"
        />
        <StatTile
          label="Failure modes"
          value={data.failure_modes.length}
          icon={TrendingDown}
          tone="danger"
        />
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <Card className="p-5">
          <SectionLabel>Success patterns</SectionLabel>
          {data.success_patterns.length === 0 ? (
            <div className="mt-2">
              <EmptyState
                title="No success patterns yet"
                hint="Patterns emerge once enough decisions have known outcomes."
              />
            </div>
          ) : (
            <ul className="mt-4 space-y-3">
              {data.success_patterns.map((p, i) => (
                <li key={i} className="rounded-lg border border-border p-3">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-sm font-medium text-heading">{p.pattern}</span>
                    <span className="shrink-0 text-xs tabular-nums text-success">
                      {Math.round(p.confidence * 100)}% conf
                    </span>
                  </div>
                  {p.indicators?.length > 0 && (
                    <p className="mt-1 text-xs leading-relaxed text-muted">
                      {p.indicators.join(" · ")}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="p-5">
          <SectionLabel>Failure modes</SectionLabel>
          {data.failure_modes.length === 0 ? (
            <div className="mt-2">
              <EmptyState title="No failure modes identified" />
            </div>
          ) : (
            <ul className="mt-4 space-y-3">
              {data.failure_modes.map((m, i) => (
                <li key={i} className="rounded-lg border border-border p-3">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-sm font-medium text-heading">{m.mode}</span>
                    <span className="shrink-0 text-xs tabular-nums text-danger">
                      {Math.round(m.frequency * 100)}% of cases
                    </span>
                  </div>
                  {m.indicators?.length > 0 && (
                    <p className="mt-1 text-xs leading-relaxed text-muted">
                      {m.indicators.join(" · ")}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
