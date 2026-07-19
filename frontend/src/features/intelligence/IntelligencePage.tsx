import { useFounder, useFounderIntelligence } from "@/api/hooks";
import { Avatar } from "@/components/founder/Avatar";
import { AnomalyPanel, FlagsPanel, MomentumPanel } from "@/components/intelligence/SignalPanel";
import { ProbabilityBars } from "@/components/intelligence/ProbabilityBars";
import { RiskRadar } from "@/components/intelligence/RiskRadar";
import { TimingVerdict } from "@/components/intelligence/TimingVerdict";
import { Card, SectionLabel, Spinner } from "@/components/ui/primitives";
import { ArrowLeft, Brain } from "lucide-react";
import { Link, useParams } from "react-router-dom";

export default function IntelligencePage() {
  const id = Number(useParams().id);
  const { data: f } = useFounder(id);
  const { data, isLoading, isError, error } = useFounderIntelligence(id);

  if (isLoading)
    return (
      <div className="flex flex-col items-center gap-3 py-24">
        <Spinner className="h-6 w-6 text-accent" />
        <p className="text-xs text-faint">Running signal, risk & predictive engines…</p>
      </div>
    );

  if (isError || !data)
    return (
      <Card className="p-6">
        <div className="text-sm font-medium text-danger">Intelligence unavailable</div>
        <p className="mt-1 text-xs text-muted">{String(error)}</p>
      </Card>
    );

  const { analysis, success, risk, timing, anomalies } = data;

  return (
    <div className="space-y-6">
      <Link
        to={`/founders/${id}`}
        className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" /> {f?.name ?? "Founder"}
      </Link>

      <header className="flex items-center gap-3">
        {f && <Avatar profile={f.profile} name={f.name} size="md" />}
        <div>
          <h1 className="flex items-center gap-2 font-display text-xl font-semibold text-heading">
            <Brain className="h-5 w-5 text-accent" /> Intelligence
          </h1>
          <p className="text-xs text-muted">
            Signal correlation, predictive modelling, risk & anomaly detection
            {f && <> · {f.name}</>}
          </p>
        </div>
      </header>

      {/* Verdict first — it is the decision the rest of the page justifies. */}
      <TimingVerdict t={timing} />

      {/* items-start keeps each card at its natural height instead of
          stretching the shorter one to leave a void. */}
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <ProbabilityBars p={success} />
        <RiskRadar risk={risk} />
      </div>

      {/* items-start keeps each card at its natural height instead of
          stretching the shorter one to leave a void. */}
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <FlagsPanel a={analysis} />
        <MomentumPanel a={analysis} />
      </div>

      {/* items-start keeps each card at its natural height instead of
          stretching the shorter one to leave a void. */}
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <AnomalyPanel r={anomalies} />

        <Card className="p-5">
          <SectionLabel>Drivers & risk factors</SectionLabel>
          <div className="mt-4 space-y-4">
            {success.key_drivers.length > 0 && (
              <div>
                <div className="mb-1.5 text-[11px] uppercase tracking-wide text-faint">
                  Key drivers
                </div>
                <ul className="space-y-1">
                  {success.key_drivers.map((d, i) => (
                    <li key={i} className="text-xs leading-relaxed text-muted">· {d}</li>
                  ))}
                </ul>
              </div>
            )}
            {success.risk_factors.length > 0 && (
              <div>
                <div className="mb-1.5 text-[11px] uppercase tracking-wide text-faint">
                  Risk factors
                </div>
                <ul className="space-y-1">
                  {success.risk_factors.map((d, i) => (
                    <li key={i} className="text-xs leading-relaxed text-muted">· {d}</li>
                  ))}
                </ul>
              </div>
            )}
            {success.key_drivers.length === 0 && success.risk_factors.length === 0 && (
              <p className="text-xs text-faint">
                No drivers isolated yet — the model needs more signals.
              </p>
            )}
          </div>
        </Card>
      </div>

      <p className="pb-2 text-center text-[11px] text-faint">
        Model output, not a decision. Every figure derives from ingested signals — absent
        data is reported as unknown, never inferred.
      </p>
    </div>
  );
}
