import { useThesis, useUpdateThesis } from "@/api/hooks";
import { Card, SectionLabel, Spinner } from "@/components/ui/primitives";
import { Check } from "lucide-react";
import { useEffect, useState } from "react";

const RISK = ["conservative", "moderate", "aggressive"];

export default function ThesisPage() {
  const { data, isLoading } = useThesis();
  const update = useUpdateThesis();

  const [sectors, setSectors] = useState("");
  const [stages, setStages] = useState("");
  const [geographies, setGeographies] = useState("");
  const [checkMin, setCheckMin] = useState("");
  const [checkMax, setCheckMax] = useState("");
  const [ownership, setOwnership] = useState("");
  const [risk, setRisk] = useState("moderate");

  useEffect(() => {
    if (!data) return;
    setSectors(data.sectors.join(", "));
    setStages(data.stages.join(", "));
    setGeographies(data.geographies.join(", "));
    setCheckMin(data.check_size_min?.toString() ?? "");
    setCheckMax(data.check_size_max?.toString() ?? "");
    setOwnership(data.ownership_target != null ? String(data.ownership_target * 100) : "");
    setRisk(data.risk_appetite);
  }, [data]);

  const list = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

  const save = () =>
    update.mutate({
      sectors: list(sectors),
      stages: list(stages),
      geographies: list(geographies),
      check_size_min: checkMin ? Number(checkMin) : null,
      check_size_max: checkMax ? Number(checkMax) : null,
      ownership_target: ownership ? Number(ownership) / 100 : null,
      risk_appetite: risk,
    });

  if (isLoading)
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-6 w-6 text-muted" />
      </div>
    );

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-heading">Investment Thesis</h1>
        <p className="mt-0.5 text-sm text-muted">
          Applied identically to inbound and outbound founders. Changes re-rank the deal flow.
        </p>
      </header>

      <Card className="space-y-5 p-6">
        <Field label="Sectors" hint="comma-separated, e.g. AI, FinTech, DevTools">
          <input className="input w-full" value={sectors} onChange={(e) => setSectors(e.target.value)} />
        </Field>
        <Field label="Stages" hint="e.g. pre-seed, seed">
          <input className="input w-full" value={stages} onChange={(e) => setStages(e.target.value)} />
        </Field>
        <Field label="Geographies" hint="e.g. Europe, US">
          <input
            className="input w-full"
            value={geographies}
            onChange={(e) => setGeographies(e.target.value)}
          />
        </Field>

        <div className="grid grid-cols-3 gap-4">
          <Field label="Check min ($)">
            <input className="input w-full" value={checkMin} onChange={(e) => setCheckMin(e.target.value)} />
          </Field>
          <Field label="Check max ($)">
            <input className="input w-full" value={checkMax} onChange={(e) => setCheckMax(e.target.value)} />
          </Field>
          <Field label="Ownership target (%)">
            <input
              className="input w-full"
              value={ownership}
              onChange={(e) => setOwnership(e.target.value)}
            />
          </Field>
        </div>

        <Field label="Risk appetite">
          <div className="flex gap-2">
            {RISK.map((r) => (
              <button
                key={r}
                onClick={() => setRisk(r)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                  risk === r ? "bg-accent text-white" : "border border-border text-muted hover:text-ink"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </Field>

        <div className="flex items-center gap-3 border-t border-border pt-4">
          <button className="btn-primary" disabled={update.isPending} onClick={save}>
            {update.isPending ? <Spinner className="h-4 w-4" /> : <Check className="h-4 w-4" />}
            Save thesis
          </button>
          {update.isSuccess && <span className="text-xs text-success">Saved · deal flow re-ranked</span>}
        </div>
      </Card>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <SectionLabel>{label}</SectionLabel>
      {hint && <div className="mb-1.5 mt-0.5 text-[11px] text-faint">{hint}</div>}
      {!hint && <div className="mb-1.5" />}
      {children}
    </div>
  );
}
