import { useDashboard, useGenerateMemo, useScoreOpportunity } from "@/api/hooks";
import type { Opportunity } from "@/api/types";
import { TripleAxis, TrendArrow, TrustRing } from "@/components/scores/ScoreViz";
import { Card, EmptyState, Pill, SectionLabel, Spinner, StatTile } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import { FileText, Gauge, GitBranch, Snowflake, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

type Filter = "all" | "cold_start" | "outbound" | "scored";

export default function DashboardPage() {
  const { data, isLoading } = useDashboard();
  const [filter, setFilter] = useState<Filter>("all");
  const [q, setQ] = useState("");

  const rows = useMemo(() => {
    let r = data?.opportunities ?? [];
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
    return r;
  }, [data, filter, q]);

  const stats = useMemo(() => {
    const all = data?.opportunities ?? [];
    return {
      total: all.length,
      scored: all.filter((o) => Object.keys(o.axes).length > 0).length,
      coldStart: all.filter((o) => o.is_cold_start).length,
      memos: all.filter((o) => o.has_memo).length,
    };
  }, [data]);

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold text-heading">Deal Flow</h1>
          <p className="mt-0.5 text-sm text-muted">
            Ranked by thesis fit. Each opportunity scored on three independent axes.
          </p>
        </div>
        <input
          className="input w-64"
          placeholder="Search founder, company, sector…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </header>

      <div className="grid grid-cols-4 gap-4">
        <StatTile label="Opportunities" value={stats.total} sub="in pipeline" />
        <StatTile label="Scored" value={stats.scored} valueClass="text-accent-soft" sub="3-axis complete" />
        <StatTile label="Cold-start" value={stats.coldStart} valueClass="text-market" sub="no network / GitHub" />
        <StatTile label="Memos" value={stats.memos} valueClass="text-idea" sub="decision-ready" />
      </div>

      <div className="flex items-center gap-2">
        {(["all", "scored", "cold_start", "outbound"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
              filter === f ? "bg-accent text-white" : "border border-border text-muted hover:text-ink",
            )}
          >
            {{ all: "All", scored: "Scored", cold_start: "Cold-start", outbound: "Outbound" }[f]}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Spinner className="h-6 w-6 text-muted" />
        </div>
      ) : rows.length === 0 ? (
        <EmptyState title="No opportunities" hint="Run the seed script or ingest a founder to begin." />
      ) : (
        <div className="space-y-3">
          {rows.map((o) => (
            <OpportunityRow key={o.application_id} o={o} />
          ))}
        </div>
      )}
    </div>
  );
}

function OpportunityRow({ o }: { o: Opportunity }) {
  const navigate = useNavigate();
  const score = useScoreOpportunity();
  const memo = useGenerateMemo();
  const isScored = Object.keys(o.axes).length > 0;

  return (
    <Card className="p-4 transition-colors hover:border-accent/40">
      <div className="flex items-center gap-5">
        {/* Identity */}
        <button
          className="min-w-0 flex-1 text-left"
          onClick={() => navigate(`/founders/${o.founder_id}`)}
        >
          <div className="flex items-center gap-2">
            <span className="truncate font-semibold">{o.company_name}</span>
            {o.is_cold_start && (
              <Pill className="bg-market/15 text-market">
                <Snowflake className="h-3 w-3" /> Cold-start
              </Pill>
            )}
            <Pill className="bg-raised text-faint">{o.channel}</Pill>
            {o.screening_decision && (
              <Pill
                className={cn(
                  o.screening_decision === "pass" && "bg-success/10 text-success",
                  o.screening_decision === "review" && "bg-claimed/10 text-claimed",
                  o.screening_decision === "fail" && "bg-danger/10 text-danger",
                )}
              >
                screen: {o.screening_decision}
              </Pill>
            )}
          </div>
          <div className="mt-0.5 truncate text-sm text-muted">
            {o.founder_name} · {o.sector ?? "—"} · {o.stage ?? "—"} · {o.geography ?? "—"}
          </div>
        </button>

        {/* Founder score */}
        <div className="hidden w-28 shrink-0 lg:block">
          <SectionLabel>Founder Score</SectionLabel>
          <div className="mt-1 flex items-center gap-1.5">
            <span className="text-lg font-semibold tabular-nums">{o.founder_score ?? "—"}</span>
            {o.momentum && <TrendArrow trend={o.momentum} />}
          </div>
        </div>

        {/* Thesis fit */}
        <div className="hidden w-24 shrink-0 sm:block">
          <SectionLabel>Thesis Fit</SectionLabel>
          <div className="mt-1 flex items-center gap-1.5 text-lg font-semibold tabular-nums">
            <Gauge className="h-4 w-4 text-accent-soft" />
            {o.thesis_fit}
          </div>
        </div>

        {/* Three axes */}
        <div className="w-72 shrink-0">
          {isScored ? (
            <TripleAxis axes={o.axes} />
          ) : (
            <div className="text-xs text-faint">Not yet scored</div>
          )}
        </div>

        {/* Trust / actions */}
        <div className="flex w-48 shrink-0 items-center justify-end gap-3">
          {isScored && (
            <button
              title="Reasoning trace"
              className="text-faint hover:text-accent"
              onClick={() => navigate(`/trace/${o.application_id}`)}
            >
              <GitBranch className="h-4 w-4" />
            </button>
          )}
          {o.has_memo ? (
            <>
              <div className="text-right">
                <SectionLabel>Trust</SectionLabel>
                <div className="text-[11px] capitalize text-muted">{o.recommendation}</div>
              </div>
              <button onClick={() => o.memo_id && navigate(`/memos/${o.memo_id}`)}>
                <TrustRing value={o.trust_score} size={44} />
              </button>
            </>
          ) : isScored ? (
            <button
              className="btn-primary text-xs"
              disabled={memo.isPending}
              onClick={() => memo.mutate(o.application_id, { onSuccess: (m) => navigate(`/memos/${m.id}`) })}
            >
              {memo.isPending ? <Spinner className="h-3.5 w-3.5" /> : <FileText className="h-3.5 w-3.5" />}
              Memo
            </button>
          ) : (
            <button
              className="btn-ghost text-xs"
              disabled={score.isPending}
              onClick={() => score.mutate(o.application_id)}
            >
              {score.isPending ? <Spinner className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
              Score
            </button>
          )}
        </div>
      </div>
    </Card>
  );
}
