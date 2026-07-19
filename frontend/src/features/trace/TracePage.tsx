import { useTrace } from "@/api/hooks";
import type { Artifact, TraceStep } from "@/api/types";
import { ConfidencePill } from "@/components/scores/ScoreViz";
import { Card, EmptyState, Pill, SectionLabel, Spinner } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import { ArrowLeft, ExternalLink, FileText, Gavel, Radar, ShieldCheck, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

const STAGE_META: Record<string, { icon: typeof Radar; color: string }> = {
  Sourcing: { icon: Radar, color: "text-accent-soft" },
  Screening: { icon: SlidersHorizontal, color: "text-founder" },
  Diligence: { icon: ShieldCheck, color: "text-idea" },
  Decision: { icon: Gavel, color: "text-success" },
};

export default function TracePage() {
  const id = Number(useParams().id);
  const { data: trace, isLoading } = useTrace(id);

  if (isLoading || !trace)
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-6 w-6 text-muted" />
      </div>
    );

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> Deal Flow
      </Link>

      <header>
        <SectionLabel>Agentic Traceability</SectionLabel>
        <h1 className="mt-1 text-xl font-semibold text-heading">
          {trace.company_name} · reasoning trace
        </h1>
        <p className="mt-1 text-sm text-muted">
          Every conclusion below links to the exact source artifact that drove it —
          {" "}first signal to decision, {trace.signal_pool} signals in Memory.
        </p>
      </header>

      {trace.steps.length === 0 ? (
        <EmptyState title="No trace yet" hint="Score the opportunity to generate a reasoning chain." />
      ) : (
        <ol className="relative space-y-3 border-l border-border pl-6">
          {trace.steps.map((step, i) => (
            <StepCard key={i} step={step} index={i + 1} />
          ))}
        </ol>
      )}
    </div>
  );
}

function StepCard({ step, index }: { step: TraceStep; index: number }) {
  const [open, setOpen] = useState(false);
  const meta = STAGE_META[step.stage] ?? STAGE_META.Screening;
  const Icon = meta.icon;
  const artifacts = step.evidence.filter(Boolean) as Artifact[];

  return (
    <li className="relative">
      {/* timeline node */}
      <span className="absolute -left-[31px] top-3 flex h-5 w-5 items-center justify-center rounded-full border border-border bg-surface">
        <Icon className={cn("h-3 w-3", meta.color)} />
      </span>

      <Card className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-wide text-faint">
                {index}. {step.stage}
              </span>
            </div>
            <div className="mt-0.5 font-semibold">{step.title}</div>
            {step.rationale && (
              <p className="mt-1 text-sm leading-relaxed text-muted">{step.rationale}</p>
            )}
          </div>
          <Pill className="shrink-0 bg-raised font-semibold text-ink">{step.conclusion}</Pill>
        </div>

        {artifacts.length > 0 && (
          <div className="mt-3 border-t border-border pt-3">
            <button
              className="text-xs font-medium text-accent hover:text-accent-soft"
              onClick={() => setOpen((v) => !v)}
            >
              {open ? "Hide" : "Show"} {artifacts.length} source artifact{artifacts.length > 1 ? "s" : ""}
            </button>
            {open && (
              <div className="mt-2 space-y-2">
                {artifacts.map((a) => (
                  <ArtifactCard key={a.signal_id} a={a} />
                ))}
              </div>
            )}
          </div>
        )}
        {step.memo_id != null && (
          <div className="mt-3 border-t border-border pt-3">
            <Link
              to={`/memos/${step.memo_id}`}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-accent hover:text-accent-soft"
            >
              <FileText className="h-3.5 w-3.5" /> Open full memo
            </Link>
          </div>
        )}
      </Card>
    </li>
  );
}

function ArtifactCard({ a }: { a: Artifact }) {
  return (
    <div className="rounded-lg border border-border/60 bg-raised/40 px-3 py-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-muted">{a.source} #{a.signal_id}</span>
          <ConfidencePill confidence={a.confidence} />
        </div>
        {a.external_url && (
          <a
            href={a.external_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-[11px] text-muted hover:text-ink"
          >
            source <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
      <p className="mt-1 text-xs leading-relaxed text-ink">{a.excerpt}</p>
    </div>
  );
}
