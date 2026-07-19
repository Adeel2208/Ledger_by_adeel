import type { WorkHistoryEntry } from "@/api/types";
import { Card, EmptyState, SectionLabel } from "@/components/ui/primitives";

/** Founder-supplied career timeline, most recent first. */
export function WorkHistory({ entries }: { entries: WorkHistoryEntry[] }) {
  return (
    <Card className="p-5">
      <SectionLabel>Track record · founder-supplied</SectionLabel>
      {entries.length === 0 ? (
        <div className="mt-4">
          <EmptyState
            title="No work history supplied"
            hint="Shown when the founder provides it — never inferred or scraped."
          />
        </div>
      ) : (
        <ol className="mt-4 space-y-4">
          {entries.map((e, i) => (
            <li key={i} className="relative pl-5">
              {/* Timeline rail: dot per role, connector on all but the last. */}
              <span className="absolute left-0 top-1.5 h-2 w-2 rounded-full bg-accent" />
              {i < entries.length - 1 && (
                <span className="absolute left-[3px] top-4 h-full w-px bg-border" />
              )}
              <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                <span className="text-sm font-medium text-heading">
                  {e.title ?? "—"}
                  {e.company && <span className="font-normal text-muted"> · {e.company}</span>}
                </span>
                {(e.start || e.end) && (
                  <span className="text-xs tabular-nums text-faint">
                    {e.start ?? "?"} – {e.end ?? "present"}
                  </span>
                )}
              </div>
              {e.summary && <p className="mt-1 text-xs leading-relaxed text-muted">{e.summary}</p>}
            </li>
          ))}
        </ol>
      )}
    </Card>
  );
}
