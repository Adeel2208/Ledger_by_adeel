import type { RiskAssessment } from "@/api/types";
import { Card, Pill, SectionLabel } from "@/components/ui/primitives";
import { HelpCircle, ShieldAlert, ShieldCheck } from "lucide-react";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const DIMENSIONS: { key: keyof RiskAssessment["risk_dimensions"]; label: string }[] = [
  { key: "execution", label: "Execution" },
  { key: "market_timing", label: "Timing" },
  { key: "team", label: "Team" },
  { key: "competitive", label: "Competitive" },
  { key: "financial", label: "Financial" },
];

const LEVEL_STYLE: Record<string, { cls: string; icon: typeof ShieldAlert; label: string }> = {
  low: { cls: "bg-success/12 text-success", icon: ShieldCheck, label: "Low risk" },
  medium: { cls: "bg-idea/12 text-idea", icon: ShieldAlert, label: "Medium risk" },
  high: { cls: "bg-danger/12 text-danger", icon: ShieldAlert, label: "High risk" },
  critical: { cls: "bg-danger/20 text-danger", icon: ShieldAlert, label: "Critical risk" },
  unknown: { cls: "bg-raised text-muted", icon: HelpCircle, label: "Risk undetermined" },
};

/**
 * Risk across five dimensions.
 *
 * "unknown" is a real state, not zero risk: with no signals ingested the engine
 * cannot assess risk, and drawing a flat zero polygon would read as "no risk
 * anywhere" — the opposite of the truth. In that case we suppress the plot and
 * say so in words.
 */
export function RiskRadar({ risk }: { risk: RiskAssessment }) {
  const meta = LEVEL_STYLE[risk.risk_level] ?? LEVEL_STYLE.unknown;
  const Icon = meta.icon;
  const undetermined = risk.risk_level === "unknown";

  const data = DIMENSIONS.map((d) => ({
    dimension: d.label,
    risk: Math.round(risk.risk_dimensions[d.key] * 100),
  }));

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <SectionLabel>Risk profile</SectionLabel>
        <Pill className={meta.cls}>
          <Icon className="h-3 w-3" /> {meta.label}
          {!undetermined && ` · ${Math.round(risk.overall_risk * 100)}`}
        </Pill>
      </div>

      {undetermined ? (
        <p className="mt-4 text-sm text-muted">
          No signals ingested yet — risk is undetermined.{" "}
          <span className="text-faint">Not low, and not high.</span>
        </p>
      ) : (
        <>
          <div className="mt-2 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={data} outerRadius="72%">
                <PolarGrid stroke="#e9e8f4" />
                <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: "#6b6a86" }} />
                <Tooltip
                  formatter={(v: number) => [`${v} / 100`, "risk"]}
                  contentStyle={{
                    background: "#ffffff",
                    border: "1px solid #e9e8f4",
                    borderRadius: 8,
                    fontSize: 12,
                    color: "#1e1b4b",
                  }}
                />
                <Radar dataKey="risk" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.22} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Direct values: the fill alone is below 3:1 on this surface. */}
          <div className="grid grid-cols-5 gap-1 border-t border-border pt-3">
            {data.map((d) => (
              <div key={d.dimension} className="text-center">
                <div className="font-display text-sm font-semibold tabular-nums text-heading">{d.risk}</div>
                <div className="text-[10px] leading-tight text-faint">{d.dimension}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {risk.mitigation_suggestions.length > 0 && (
        <ul className="mt-4 space-y-1.5 border-t border-border pt-3">
          {risk.mitigation_suggestions.slice(0, 3).map((m, i) => (
            <li key={i} className="text-xs leading-relaxed text-muted">
              · {m}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
