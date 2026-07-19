import { useFounder } from "@/api/hooks";
import { TrendArrow, ConfidencePill } from "@/components/scores/ScoreViz";
import { Card, EmptyState, Pill, SectionLabel, Spinner, StatTile } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import { ArrowLeft, ExternalLink, Snowflake } from "lucide-react";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link, useParams } from "react-router-dom";

export default function FounderPage() {
  const id = Number(useParams().id);
  const { data: f, isLoading } = useFounder(id);

  if (isLoading || !f)
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-6 w-6 text-muted" />
      </div>
    );

  const history = f.score_history.map((p, i) => ({
    i: i + 1,
    value: p.value,
    date: new Date(p.computed_at).toLocaleDateString(),
  }));

  return (
    <div className="space-y-6">
      <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> Deal Flow
      </Link>

      <header className="flex items-center gap-3">
        <h1 className="text-xl font-semibold text-heading">{f.name}</h1>
        {f.is_cold_start && (
          <Pill className="bg-market/15 text-market">
            <Snowflake className="h-3 w-3" /> Cold-start · alternate scoring
          </Pill>
        )}
      </header>

      <div className="grid grid-cols-4 gap-4">
        <StatTile
          label="Persistent Founder Score"
          value={
            <span className="flex items-center gap-2">
              {f.founder_score ?? "—"}
              {f.momentum && <TrendArrow trend={f.momentum} />}
            </span>
          }
          sub="follows the founder across ventures — never resets"
          valueClass="text-accent-soft"
        />
        <StatTile label="Signals" value={f.data_quality.signal_count} sub="evidence points ingested" />
        <StatTile label="Covered facets" value={f.data_quality.covered.length} valueClass="text-success" />
        <StatTile label="Data gaps" value={f.data_quality.gaps.length} valueClass="text-danger" sub="disclosed, not fabricated" />
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Components + history */}
        <div className="col-span-2 space-y-6">
          <Card className="p-5">
            <SectionLabel>Score composition (observed components)</SectionLabel>
            <div className="mt-4 space-y-3">
              {Object.entries(f.components)
                .filter(([, v]) => v > 0)
                .sort((a, b) => b[1] - a[1])
                .map(([k, v]) => (
                  <div key={k}>
                    <div className="mb-1 flex justify-between text-xs">
                      <span className="capitalize text-muted">{k}</span>
                      <span className="tabular-nums">{v}</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-raised">
                      <div className="h-full rounded-full bg-accent" style={{ width: `${v}%` }} />
                    </div>
                  </div>
                ))}
            </div>
            <p className="mt-4 text-[11px] leading-relaxed text-faint">
              Absent components (e.g. no GitHub for a cold-start founder) are treated as unknown,
              not zero — they are never averaged in to penalize missing traditional signals.
            </p>
          </Card>

          <Card className="p-5">
            <SectionLabel>Score trajectory</SectionLabel>
            <div className="mt-4 h-48">
              {history.length > 1 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#e2e8f0" />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#e2e8f0" />
                    <Tooltip
                      contentStyle={{
                        background: "#ffffff",
                        border: "1px solid #e4e7ec",
                        borderRadius: 8,
                        fontSize: 12,
                        color: "#1a1d24",
                      }}
                    />
                    <Line type="monotone" dataKey="value" stroke="#1e40af" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState title="Single data point" hint="Momentum appears after re-scoring over time." />
              )}
            </div>
          </Card>
        </div>

        {/* Data quality */}
        <Card className="h-fit p-5">
          <SectionLabel>Data quality</SectionLabel>
          <div className="mt-3 space-y-4 text-sm">
            <div>
              <div className="mb-1.5 text-xs text-faint">Reliability mix</div>
              <div className="flex flex-wrap items-center gap-2">
                {Object.entries(f.data_quality.reliability_mix).length === 0 && (
                  <span className="text-xs text-faint">—</span>
                )}
                {Object.entries(f.data_quality.reliability_mix).map(([k, n]) => (
                  <span key={k} className="flex items-center gap-1">
                    <ConfidencePill confidence={k as never} />
                    <span className="text-xs text-faint">×{n}</span>
                  </span>
                ))}
              </div>
            </div>
            {f.data_quality.gaps.length > 0 && (
              <div>
                <div className="mb-1.5 text-xs text-faint">Disclosed gaps</div>
                <div className="flex flex-wrap gap-1.5">
                  {f.data_quality.gaps.map((g) => (
                    <Pill key={g} className="bg-danger/10 text-danger">
                      {g.replace(/_/g, " ")}
                    </Pill>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Signals */}
      <Card className="p-5">
        <SectionLabel>Evidence signals · provenance</SectionLabel>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-faint">
                <th className="pb-2 pr-4 font-medium">Source</th>
                <th className="pb-2 pr-4 font-medium">Type</th>
                <th className="pb-2 pr-4 font-medium">Confidence</th>
                <th className="pb-2 pr-4 font-medium">Detail</th>
                <th className="pb-2 font-medium">Seen</th>
              </tr>
            </thead>
            <tbody>
              {f.signals.map((s) => (
                <tr key={s.id} className="border-b border-border/50 last:border-0">
                  <td className="py-2 pr-4">
                    <span className="font-mono text-xs text-muted">{s.source}</span>
                  </td>
                  <td className="py-2 pr-4 text-xs text-muted">{s.record_type}</td>
                  <td className="py-2 pr-4">
                    <ConfidencePill confidence={s.confidence} />
                  </td>
                  <td className="max-w-md py-2 pr-4">
                    <span className="line-clamp-1 text-muted">
                      {String((s.payload as { text?: string })?.text ?? "")}
                    </span>
                  </td>
                  <td className="py-2 text-xs text-faint">
                    {s.external_url ? (
                      <a
                        href={s.external_url}
                        target="_blank"
                        rel="noreferrer"
                        className={cn("inline-flex items-center gap-1 hover:text-ink")}
                      >
                        {new Date(s.timestamp).toLocaleDateString()}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    ) : (
                      new Date(s.timestamp).toLocaleDateString()
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
