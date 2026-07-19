import { useDashboard, useGenerateMemo, useScoreOpportunity } from "@/api/hooks";
import type { Opportunity } from "@/api/types";
import { TrendArrow, TrustRing } from "@/components/scores/ScoreViz";
import { Card, EmptyState, Pill, SectionLabel, Spinner } from "@/components/ui/primitives";
import { cn, scoreColor } from "@/lib/utils";
import {
  ChevronDown,
  ChevronUp,
  FileText,
  Gauge,
  GitBranch,
  Layers,
  Search,
  ShieldCheck,
  Snowflake,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { KpiTile, MiniAxes, PipelineFunnel, PortfolioAxes, SourcingDonut } from "./widgets";

type Filter = "all" | "cold_start" | "outbound" | "scored";
type SortKey = "thesis_fit" | "founder_score" | "trust_score" | "founder" | "market" | "idea" | "company_name";

const mean = (xs: (number | null | undefined)[]) => {
  const v = xs.filter((x): x is number => x != null);
  return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
};

export default function DashboardPage() {
  const { data, isLoading } = useDashboard();
  const [filter, setFilter] = useState<Filter>("all");
  const [q, setQ] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("thesis_fit");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const opps = data?.opportunities ?? [];

  const m = useMemo(() => {
    const scored = opps.filter((o) => Object.keys(o.axes).length > 0);
    const screened = opps.filter((o) => o.screening_decision);
    const passes = opps.filter((o) => o.screening_decision === "pass");
    return {
      total: opps.length,
      scored: scored.length,
      coldStart: opps.filter((o) => o.is_cold_start).length,
      memos: opps.filter((o) => o.has_memo).length,
      avgFounder: mean(opps.map((o) => o.founder_score)),
      avgFit: mean(opps.map((o) => o.thesis_fit)),
      avgTrust: mean(opps.map((o) => o.trust_score)),
      passRate: screened.length ? Math.round((passes.length / screened.length) * 100) : 0,
      pipeline: [
        { label: "Sourced", count: opps.length },
        { label: "Screened", count: screened.length },
        { label: "Scored", count: scored.length },
        { label: "Decision", count: opps.filter((o) => o.has_memo).length },
      ],
      sourcing: [
        { name: "inbound", value: opps.filter((o) => o.channel === "inbound").length },
        { name: "outbound", value: opps.filter((o) => o.channel === "outbound").length },
      ].filter((d) => d.value > 0),
      avgAxes: {
        founder: mean(scored.map((o) => o.axes.founder?.value)),
        market: mean(scored.map((o) => o.axes.market?.value)),
        idea: mean(scored.map((o) => o.axes.idea?.value)),
      },
    };
  }, [opps]);

  const rows = useMemo(() => {
    let r = [...opps];
    if (filter === "cold_start") r = r.filter((o) => o.is_cold_start);
    if (filter === "outbound") r = r.filter((o) => o.channel === "outbound");
    if (filter === "scored") r = r.filter((o) => Object.keys(o.axes).length > 0);
    if (q.trim()) {
      const s = q.toLowerCase();
      r = r.filter(
        (o) =>
          o.founder_name.toLowerCase().includes(s) ||
          o.company_name.toLowerCase().includes(s) ||
          (o.sector ?? "").toLowerCase().includes(s),
      );
    }
    const get = (o: Opportunity): number | string => {
      if (sortKey === "company_name") return o.company_name.toLowerCase();
      if (sortKey === "founder" || sortKey === "market" || sortKey === "idea")
        return o.axes[sortKey]?.value ?? -1;
      return (o[sortKey] as number) ?? -1;
    };
    r.sort((a, b) => {
      const va = get(a), vb = get(b);
      const cmp = va < vb ? -1 : va > vb ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });
    return r;
  }, [opps, filter, q, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir(key === "company_name" ? "asc" : "desc");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-tight">
            <span className="gradient-text">Deal Flow</span>
          </h1>
          <p className="mt-1 text-sm text-muted">
            Live pipeline · {m.total} opportunities · scored on three independent axes.
          </p>
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-faint" />
          <input
            className="input w-72 pl-10"
            placeholder="Search founder, company, sector…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
      </header>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <KpiTile label="Opportunities" value={m.total} icon={Layers} tone="brand" gradient />
        <KpiTile label="Avg Founder" value={m.avgFounder?.toFixed(0) ?? "—"} icon={TrendingUp} tone="founder" />
        <KpiTile label="Avg Thesis Fit" value={m.avgFit?.toFixed(0) ?? "—"} icon={Target} tone="cyan" />
        <KpiTile label="Pass Rate" value={`${m.passRate}%`} icon={Gauge} tone="market" />
        <KpiTile label="Avg Trust" value={m.avgTrust?.toFixed(0) ?? "—"} icon={ShieldCheck} tone="idea" />
        <KpiTile label="Cold-start" value={m.coldStart} icon={Snowflake} tone="cyan" />
      </div>

      {/* Insight panels */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="p-5">
          <SectionLabel>Pipeline · Sourcing → Decision</SectionLabel>
          <div className="mt-4">
            <PipelineFunnel stages={m.pipeline} />
          </div>
        </Card>
        <Card className="p-5">
          <SectionLabel>Sourcing mix</SectionLabel>
          <div className="mt-4">
            <SourcingDonut data={m.sourcing} centerLabel="total" centerValue={m.total} />
          </div>
        </Card>
        <Card className="p-5">
          <SectionLabel>Portfolio strength (avg)</SectionLabel>
          <div className="mt-4">
            <PortfolioAxes avg={m.avgAxes} />
          </div>
        </Card>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {(["all", "scored", "cold_start", "outbound"] as Filter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "rounded-full px-4 py-1.5 text-xs font-semibold transition-all duration-200",
                filter === f
                  ? "bg-brand text-white shadow-ring"
                  : "border border-border bg-surface text-muted hover:border-accent/40 hover:text-accent",
              )}
            >
              {{ all: "All", scored: "Scored", cold_start: "Cold-start", outbound: "Outbound" }[f]}
            </button>
          ))}
        </div>
        <span className="text-xs text-faint">{rows.length} shown</span>
      </div>

      {/* Deal table */}
      {isLoading ? (
        <div className="flex justify-center py-24"><Spinner className="h-6 w-6 text-accent" /></div>
      ) : rows.length === 0 ? (
        <EmptyState title="No opportunities" hint="Run the seed script or ingest a founder to begin." />
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-sm">
              <thead>
                <tr className="border-b border-border bg-raised/40 text-left text-[11px] uppercase tracking-wide text-faint">
                  <Th onClick={() => toggleSort("company_name")} active={sortKey === "company_name"} dir={sortDir}>Opportunity</Th>
                  <th className="px-3 py-3 font-semibold">Sector · Stage · Geo</th>
                  <th className="px-3 py-3 font-semibold">Channel</th>
                  <Th onClick={() => toggleSort("founder_score")} active={sortKey === "founder_score"} dir={sortDir} right>Founder</Th>
                  <Th onClick={() => toggleSort("thesis_fit")} active={sortKey === "thesis_fit"} dir={sortDir} right>Fit</Th>
                  <th className="px-3 py-3 text-center font-semibold">3-Axis</th>
                  <Th onClick={() => toggleSort("trust_score")} active={sortKey === "trust_score"} dir={sortDir} center>Trust</Th>
                  <th className="px-3 py-3 font-semibold">Rec.</th>
                  <th className="px-3 py-3 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((o) => (
                  <DealRow key={o.application_id} o={o} />
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function Th({
  children,
  onClick,
  active,
  dir,
  right,
  center,
}: {
  children: React.ReactNode;
  onClick: () => void;
  active: boolean;
  dir: "asc" | "desc";
  right?: boolean;
  center?: boolean;
}) {
  return (
    <th className={cn("px-3 py-3 font-semibold", right && "text-right", center && "text-center")}>
      <button
        onClick={onClick}
        className={cn(
          "inline-flex items-center gap-1 uppercase transition-colors hover:text-accent",
          active && "text-accent",
        )}
      >
        {children}
        {active && (dir === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
      </button>
    </th>
  );
}

const REC_BADGE: Record<string, string> = {
  invest: "bg-success/12 text-success ring-1 ring-success/20",
  pass: "bg-danger/12 text-danger ring-1 ring-danger/20",
  need_more_info: "bg-claimed/12 text-claimed ring-1 ring-claimed/20",
};

function DealRow({ o }: { o: Opportunity }) {
  const navigate = useNavigate();
  const score = useScoreOpportunity();
  const memo = useGenerateMemo();
  const isScored = Object.keys(o.axes).length > 0;

  return (
    <tr className="border-b border-border/60 transition-colors last:border-0 hover:bg-brand-soft/40">
      {/* Opportunity */}
      <td className="px-3 py-3">
        <button className="text-left" onClick={() => navigate(`/founders/${o.founder_id}`)}>
          <div className="flex items-center gap-2">
            <span className="font-display font-semibold text-heading hover:text-accent">{o.company_name}</span>
            {o.is_cold_start && (
              <Pill className="bg-market/12 text-market ring-1 ring-market/20">
                <Snowflake className="h-2.5 w-2.5" /> Cold
              </Pill>
            )}
          </div>
          <div className="mt-0.5 text-xs text-muted">{o.founder_name}</div>
        </button>
      </td>
      {/* Sector/Stage/Geo */}
      <td className="px-3 py-3 text-xs text-muted">
        <div className="text-ink">{o.sector ?? "—"}</div>
        <div className="text-faint">{o.stage ?? "—"} · {o.geography ?? "—"}</div>
      </td>
      {/* Channel */}
      <td className="px-3 py-3">
        <Pill className="bg-raised capitalize text-muted">{o.channel}</Pill>
      </td>
      {/* Founder score */}
      <td className="px-3 py-3 text-right">
        <div className="flex items-center justify-end gap-1">
          <span className={cn("font-display text-base font-bold tabular-nums", scoreColor(o.founder_score))}>
            {o.founder_score ?? "—"}
          </span>
          {o.momentum && <TrendArrow trend={o.momentum} className="h-3.5 w-3.5" />}
        </div>
      </td>
      {/* Thesis fit */}
      <td className="px-3 py-3 text-right">
        <span className={cn("font-display text-base font-bold tabular-nums", scoreColor(o.thesis_fit))}>
          {o.thesis_fit}
        </span>
      </td>
      {/* 3-axis mini */}
      <td className="px-3 py-3">
        <div className="flex justify-center"><MiniAxes axes={o.axes} /></div>
      </td>
      {/* Trust */}
      <td className="px-3 py-3">
        <div className="flex justify-center">
          {o.has_memo ? (
            <button onClick={() => o.memo_id && navigate(`/memos/${o.memo_id}`)} className="transition-transform hover:scale-105">
              <TrustRing value={o.trust_score} size={40} />
            </button>
          ) : (
            <span className="text-xs text-faint">—</span>
          )}
        </div>
      </td>
      {/* Recommendation */}
      <td className="px-3 py-3">
        {o.recommendation ? (
          <Pill className={REC_BADGE[o.recommendation] ?? "bg-raised text-muted"}>
            {o.recommendation.replace(/_/g, " ")}
          </Pill>
        ) : (
          <span className="text-xs text-faint">—</span>
        )}
      </td>
      {/* Actions */}
      <td className="px-3 py-3">
        <div className="flex items-center justify-end gap-1.5">
          {isScored && (
            <button
              title="Reasoning trace"
              className="rounded-lg p-1.5 text-faint transition-colors hover:bg-raised hover:text-accent"
              onClick={() => navigate(`/trace/${o.application_id}`)}
            >
              <GitBranch className="h-4 w-4" />
            </button>
          )}
          {o.has_memo ? (
            <button className="btn-ghost px-3 py-1.5 text-xs" onClick={() => o.memo_id && navigate(`/memos/${o.memo_id}`)}>
              Memo
            </button>
          ) : isScored ? (
            <button
              className="btn-primary px-3 py-1.5 text-xs"
              disabled={memo.isPending}
              onClick={() => memo.mutate(o.application_id, { onSuccess: (mm) => navigate(`/memos/${mm.id}`) })}
            >
              {memo.isPending ? <Spinner className="h-3.5 w-3.5" /> : <FileText className="h-3.5 w-3.5" />}
              Memo
            </button>
          ) : (
            <button
              className="btn-primary px-3 py-1.5 text-xs"
              disabled={score.isPending}
              onClick={() => score.mutate(o.application_id)}
            >
              {score.isPending ? <Spinner className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
              Score
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
