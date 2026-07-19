import { useChannelAnalytics } from "@/api/hooks";
import { Card, EmptyState, Pill, SectionLabel, Spinner } from "@/components/ui/primitives";
import { Lightbulb } from "lucide-react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const CHANNEL_COLOR: Record<string, string> = { inbound: "#3b82f6", outbound: "#1e40af" };

export default function AnalyticsPage() {
  const { data, isLoading } = useChannelAnalytics();

  if (isLoading || !data)
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-6 w-6 text-muted" />
      </div>
    );

  const chartData = data.by_channel.map((c) => ({
    channel: c.channel,
    "Founder Score": c.avg_founder_score ?? 0,
    "Thesis Fit": c.avg_thesis_fit ?? 0,
  }));

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-heading">Sourcing Intelligence</h1>
        <p className="mt-0.5 text-sm text-muted">
          Which channels produce your strongest founders — and which sources to scan next.
        </p>
      </header>

      {data.suggestion && (
        <Card className="flex items-start gap-3 border-accent/30 bg-accent/5 p-4">
          <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
          <p className="text-sm text-ink">{data.suggestion}</p>
        </Card>
      )}

      {data.by_channel.length === 0 ? (
        <EmptyState title="No channel data yet" hint="Score a few opportunities to populate this view." />
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {/* Chart */}
          <Card className="col-span-2 p-5">
            <SectionLabel>Channel performance</SectionLabel>
            <div className="mt-4 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} barGap={6}>
                  <XAxis dataKey="channel" tick={{ fontSize: 12, fill: "#5b6472" }} stroke="#e2e8f0" />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#e2e8f0" />
                  <Tooltip
                    cursor={{ fill: "#f1f3f6" }}
                    contentStyle={{ background: "#fff", border: "1px solid #e4e7ec", borderRadius: 8, fontSize: 12 }}
                  />
                  <Bar dataKey="Founder Score" radius={[4, 4, 0, 0]}>
                    {chartData.map((d) => (
                      <Cell key={d.channel} fill={CHANNEL_COLOR[d.channel] ?? "#6366f1"} />
                    ))}
                  </Bar>
                  <Bar dataKey="Thesis Fit" radius={[4, 4, 0, 0]} fill="#d97706" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <table className="mt-4 w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-faint">
                  <th className="pb-2 font-medium">Channel</th>
                  <th className="pb-2 font-medium">Opps</th>
                  <th className="pb-2 font-medium">Avg founder</th>
                  <th className="pb-2 font-medium">Avg thesis</th>
                  <th className="pb-2 font-medium">Pass rate</th>
                </tr>
              </thead>
              <tbody>
                {data.by_channel.map((c) => (
                  <tr key={c.channel} className="border-b border-border/50 last:border-0">
                    <td className="py-2 font-medium capitalize">{c.channel}</td>
                    <td className="py-2 tabular-nums text-muted">{c.count}</td>
                    <td className="py-2 tabular-nums">{c.avg_founder_score ?? "—"}</td>
                    <td className="py-2 tabular-nums">{c.avg_thesis_fit ?? "—"}</td>
                    <td className="py-2 tabular-nums text-muted">{Math.round(c.pass_rate * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {/* Sources + underexplored */}
          <Card className="h-fit p-5">
            <SectionLabel>Source yield</SectionLabel>
            <div className="mt-3 space-y-2">
              {data.by_source.map((s) => (
                <div key={s.source} className="flex items-center justify-between text-sm">
                  <span className="font-mono text-xs text-muted">{s.source}</span>
                  <span className="tabular-nums">{s.founders} founder{s.founders > 1 ? "s" : ""}</span>
                </div>
              ))}
            </div>
            {data.underexplored.length > 0 && (
              <div className="mt-4 border-t border-border pt-3">
                <div className="mb-1.5 text-xs text-faint">Underexplored — scan next</div>
                <div className="flex flex-wrap gap-1.5">
                  {data.underexplored.map((s) => (
                    <Pill key={s} className="bg-cta/10 text-cta">{s}</Pill>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
