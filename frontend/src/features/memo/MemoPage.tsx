import { useMemo as useMemoQuery } from "@/api/hooks";
import type { MemoClaim, MemoSection } from "@/api/types";
import { ConfidencePill, ContradictionFlag, TrustRing } from "@/components/scores/ScoreViz";
import { Card, EmptyState, Pill, SectionLabel, Spinner } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import { AlertTriangle, ArrowLeft, ExternalLink, GitBranch, Link2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";

const REC_STYLE: Record<string, string> = {
  invest: "bg-success/15 text-success",
  pass: "bg-danger/15 text-danger",
  need_more_info: "bg-claimed/15 text-claimed",
};

export default function MemoPage() {
  const id = Number(useParams().id);
  const { data: memo, isLoading } = useMemoQuery(id);

  if (isLoading || !memo)
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-6 w-6 text-muted" />
      </div>
    );

  const rec = memo.recommendation ?? "need_more_info";

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> Deal Flow
      </Link>

      {/* Header */}
      <Card className="flex items-center justify-between p-6">
        <div>
          <SectionLabel>Investment Memo</SectionLabel>
          <div className="mt-1 flex items-center gap-3">
            <Pill className={cn("text-sm", REC_STYLE[rec])}>{rec.replace(/_/g, " ").toUpperCase()}</Pill>
          </div>
          <p className="mt-2 max-w-lg text-xs leading-relaxed text-faint">
            Every claim is evidence-traced and confidence-tiered. Missing data is disclosed, not
            fabricated. Contradictions are flagged, not silently resolved.
          </p>
          <Link
            to={`/trace/${memo.application_id}`}
            className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-accent hover:text-accent-soft"
          >
            <GitBranch className="h-3.5 w-3.5" /> View full reasoning trace
          </Link>
        </div>
        <div className="flex flex-col items-center gap-1">
          <TrustRing value={memo.trust_score} size={72} />
          <SectionLabel>Trust Score</SectionLabel>
        </div>
      </Card>

      {memo.sections.length === 0 ? (
        <EmptyState title="Empty memo" />
      ) : (
        <div className="space-y-4">
          {memo.sections.map((s, i) => (
            <SectionCard key={i} section={s} />
          ))}
        </div>
      )}
    </div>
  );
}

function SectionCard({ section }: { section: MemoSection }) {
  if (section.is_gap) {
    return (
      <div className="flex items-start gap-3 rounded-xl border border-danger/25 bg-danger/5 px-4 py-3">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-danger">Data gap</div>
          <div className="mt-0.5 text-sm text-muted">{section.body}</div>
        </div>
      </div>
    );
  }

  return (
    <Card className="p-5">
      <h2 className="text-sm font-semibold">{section.title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-muted">{section.body}</p>
      {section.claims.length > 0 && (
        <div className="mt-4 space-y-2 border-t border-border pt-4">
          {section.claims.map((c, i) => (
            <ClaimRow key={i} claim={c} />
          ))}
        </div>
      )}
    </Card>
  );
}

function ClaimRow({ claim }: { claim: MemoClaim }) {
  return (
    <div
      className={cn(
        "rounded-lg border px-3 py-2.5",
        claim.contradicted ? "border-danger/30 bg-danger/5" : "border-border/60 bg-raised/40",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm text-ink">{claim.text}</p>
        <div className="flex shrink-0 items-center gap-1.5">
          {claim.contradicted && <ContradictionFlag />}
          <ConfidencePill confidence={claim.confidence} />
        </div>
      </div>
      {claim.evidence.length > 0 && (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <Link2 className="h-3 w-3 text-faint" />
          {claim.evidence.map((e, i) =>
            e.external_url ? (
              <a
                key={i}
                href={e.external_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 rounded-md bg-raised px-2 py-0.5 text-[11px] text-muted hover:text-ink"
              >
                {e.source ?? "source"} #{e.signal_id}
                <ExternalLink className="h-2.5 w-2.5" />
              </a>
            ) : (
              <span
                key={i}
                className="rounded-md bg-raised px-2 py-0.5 text-[11px] text-muted"
              >
                {e.source ?? "source"} #{e.signal_id}
              </span>
            ),
          )}
        </div>
      )}
    </div>
  );
}
