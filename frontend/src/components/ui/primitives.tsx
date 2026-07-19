import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";
import type { ComponentType, ReactNode } from "react";

export function Card({
  className,
  hover,
  children,
}: {
  className?: string;
  hover?: boolean;
  children: ReactNode;
}) {
  return <div className={cn("card", hover && "card-hover", className)}>{children}</div>;
}

export function Pill({ className, children }: { className?: string; children: ReactNode }) {
  return <span className={cn("pill", className)}>{children}</span>;
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("animate-spin", className)} />;
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-faint">{children}</div>
  );
}

export function EmptyState({
  title,
  hint,
  compact,
}: {
  title: string;
  hint?: string;
  /** Tighter padding for empty states inside a small card, where the default
   *  full-page spacing would leave a large void. */
  compact?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-1.5 text-center",
        compact ? "py-8" : "py-20",
      )}
    >
      <div className="text-sm font-semibold text-muted">{title}</div>
      {hint && <div className="text-xs text-faint">{hint}</div>}
    </div>
  );
}

const TONES: Record<string, string> = {
  brand: "bg-brand-soft text-accent",
  founder: "bg-founder/12 text-founder",
  market: "bg-market/12 text-market",
  idea: "bg-idea/12 text-idea",
  danger: "bg-danger/12 text-danger",
};

export function StatTile({
  label,
  value,
  sub,
  icon: Icon,
  tone = "brand",
  gradient,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  icon?: ComponentType<{ className?: string }>;
  tone?: keyof typeof TONES | string;
  gradient?: boolean;
}) {
  return (
    <Card hover className="p-5">
      <div className="flex items-start justify-between">
        <SectionLabel>{label}</SectionLabel>
        {Icon && (
          <span className={cn("flex h-8 w-8 items-center justify-center rounded-lg", TONES[tone] ?? TONES.brand)}>
            <Icon className="h-4 w-4" />
          </span>
        )}
      </div>
      <div
        className={cn(
          "mt-2 font-display text-3xl font-bold tabular-nums tracking-tight",
          gradient ? "gradient-text" : "text-heading",
        )}
      >
        {value}
      </div>
      {sub && <div className="mt-0.5 text-xs text-faint">{sub}</div>}
    </Card>
  );
}
