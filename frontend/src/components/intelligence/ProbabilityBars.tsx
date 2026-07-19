import type { SuccessProbability } from "@/api/types";
import { Card, SectionLabel } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";

const MILESTONES: { key: keyof SuccessProbability["probabilities"]; label: string }[] = [
  { key: "product_market_fit", label: "Product–market fit" },
  { key: "series_a_funding", label: "Series A funding" },
  { key: "profitability", label: "Profitability" },
  { key: "exit_potential", label: "Exit potential" },
];

/**
 * Milestone probabilities as direct-labelled bars.
 *
 * Every bar carries its own percentage: the accent fill sits below 3:1 against
 * the card surface, so the number — not the colour — is what conveys the value.
 * One hue throughout, because these are magnitudes of the same measure, not
 * four distinct categories.
 */
export function ProbabilityBars({ p }: { p: SuccessProbability }) {
  const unknown = p.confidence === 0;

  return (
    <Card className="p-5">
      <div className="flex items-baseline justify-between">
        <SectionLabel>Milestone probability</SectionLabel>
        <span className="text-[11px] text-faint">
          model confidence {Math.round(p.confidence * 100)}%
        </span>
      </div>

      {unknown ? (
        <p className="mt-4 text-sm text-muted">
          Not enough signals to estimate milestones.{" "}
          <span className="text-faint">This is a data gap, not a negative finding.</span>
        </p>
      ) : (
        <div className="mt-4 space-y-3.5">
          {MILESTONES.map(({ key, label }) => {
            const v = p.probabilities[key];
            return (
              <div key={key}>
                <div className="mb-1.5 flex items-baseline justify-between text-xs">
                  <span className="text-muted">{label}</span>
                  <span className="font-display font-semibold tabular-nums text-heading">
                    {Math.round(v * 100)}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-raised">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      v >= 0.6 ? "bg-success" : v >= 0.35 ? "bg-idea" : "bg-founder",
                    )}
                    style={{ width: `${Math.max(v * 100, 1.5)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {(p.timing_estimates.months_to_pmf || p.timing_estimates.months_to_funding) && (
        <div className="mt-4 flex gap-5 border-t border-border pt-3 text-xs text-muted">
          {p.timing_estimates.months_to_pmf != null && (
            <span>
              PMF in ~<span className="tabular-nums text-heading">{p.timing_estimates.months_to_pmf}</span> mo
            </span>
          )}
          {p.timing_estimates.months_to_funding != null && (
            <span>
              Funding in ~<span className="tabular-nums text-heading">{p.timing_estimates.months_to_funding}</span> mo
            </span>
          )}
        </div>
      )}
    </Card>
  );
}
