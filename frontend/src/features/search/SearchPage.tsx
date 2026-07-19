import { useSearch } from "@/api/hooks";
import type { ParsedQuery, SearchResult } from "@/api/types";
import { Avatar } from "@/components/founder/Avatar";
import { Card, EmptyState, Pill, SectionLabel, Spinner } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import { ArrowRight, Search, Sparkles } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

/** Ready-made queries so the first visit demonstrates the feature instead of
 *  presenting a blank box. The first is the challenge brief's own example. */
const SUGGESTIONS = [
  "technical founder, Berlin, AI infra, enterprise traction, no prior VC backing",
  "cold-start founder with strong technical artifacts",
  "AI founder with GitHub momentum, pre-seed, no accelerator",
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const search = useSearch();
  const navigate = useNavigate();

  const run = (q: string) => {
    const trimmed = q.trim();
    if (!trimmed || search.isPending) return;
    setQuery(trimmed);
    search.mutate(trimmed);
  };

  const data = search.data;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="flex items-center gap-2 font-display text-xl font-semibold text-heading">
          <Search className="h-5 w-5 text-accent" /> Multi-Attribute Search
        </h1>
        <p className="mt-0.5 text-sm text-muted">
          Ask in plain language — the system parses attributes, ranges and negations, then runs
          hybrid semantic + structured search.
        </p>
      </header>

      {/* Query input */}
      <Card className="p-4">
        <div className="flex gap-2">
          <input
            className="input flex-1"
            placeholder='e.g. "technical founder, Berlin, AI infra, no prior VC backing"'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run(query)}
            autoFocus
          />
          <button
            className="btn-primary shrink-0"
            disabled={!query.trim() || search.isPending}
            onClick={() => run(query)}
          >
            {search.isPending ? <Spinner className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
            Search
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              className="rounded-full bg-raised px-3 py-1 text-xs text-muted transition-colors hover:bg-brand-soft hover:text-accent"
              onClick={() => run(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </Card>

      {search.isError && (
        <Card className="p-5">
          <div className="text-sm font-medium text-danger">Search failed</div>
          <p className="mt-1 text-xs text-muted">{String(search.error)}</p>
        </Card>
      )}

      {data && (
        <>
          <ParsedQueryCard parsed={data.parsed} />

          <div className="flex items-baseline justify-between">
            <SectionLabel>Results</SectionLabel>
            <span className="text-xs text-faint">{data.total} matched</span>
          </div>

          {data.results.length === 0 ? (
            <Card>
              <EmptyState
                title="No founders matched"
                hint="Every constraint above was applied literally — loosen one and retry."
              />
            </Card>
          ) : (
            <div className="space-y-3">
              {data.results.map((r) => (
                <ResultRow key={`${r.founder_id}-${r.company_id}`} r={r}
                           onOpen={() => navigate(`/founders/${r.founder_id}`)} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/** Chip labels for entity groups — a map, because naive `s`-stripping turns
 *  "technologies" into "technologie". */
const ENTITY_LABEL: Record<string, string> = {
  sectors: "sector",
  locations: "location",
  technologies: "technology",
  accelerators: "accelerator",
  companies: "company",
  investors: "investor",
};

/** How the parser read the query — interpretation shown, never hidden.
 *  If the parse is wrong the user can see exactly why the results are. */
function ParsedQueryCard({ parsed }: { parsed: ParsedQuery }) {
  const entityGroups = Object.entries(parsed.entities).filter(([, v]) => v.length > 0);
  const attrs = Object.entries(parsed.attributes).filter(([, v]) => v !== null);
  const ranges = Object.entries(parsed.ranges).filter(([, v]) => v !== null);
  const empty = entityGroups.length === 0 && attrs.length === 0 && ranges.length === 0 && parsed.negations.length === 0;

  return (
    <Card className="p-4">
      <div className="flex items-baseline justify-between">
        <SectionLabel>How the system read your query</SectionLabel>
        <span className="text-[11px] text-faint">
          parser confidence {Math.round(parsed.confidence * 100)}%
        </span>
      </div>

      {empty ? (
        <p className="mt-2 text-xs text-muted">
          No structured constraints detected — running purely semantic search for
          “{parsed.semantic_query}”.
        </p>
      ) : (
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          {entityGroups.flatMap(([group, values]) =>
            values.map((v: string) => (
              <Pill key={`${group}-${v}`} className="bg-brand-soft text-accent">
                {ENTITY_LABEL[group] ?? group}: {v}
              </Pill>
            )),
          )}
          {attrs.map(([k, v]) => (
            <Pill key={k} className={cn(v ? "bg-market/12 text-market" : "bg-raised text-muted")}>
              {k.replace(/^(is|has|from)_/, "").replace(/_/g, " ")}: {v ? "yes" : "no"}
            </Pill>
          ))}
          {ranges.map(([k, v]) => (
            <Pill key={k} className="bg-idea/12 text-idea">
              {k.replace(/_/g, " ")}: {Number(v).toLocaleString()}
            </Pill>
          ))}
          {parsed.negations.map((n) => (
            <Pill key={n} className="bg-danger/10 text-danger">
              not: {n.replace(/_/g, " ")}
            </Pill>
          ))}
        </div>
      )}
    </Card>
  );
}

function ResultRow({ r, onOpen }: { r: SearchResult; onOpen: () => void }) {
  const highlights = Object.entries(r.highlights);

  return (
    <Card hover className="cursor-pointer p-4" >
      <button className="flex w-full items-start gap-3 text-left" onClick={onOpen}>
        {r.avatar && <Avatar profile={r.avatar} name={r.founder_name} size="md" />}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-2">
            <span className="font-display font-semibold text-heading">{r.founder_name}</span>
            {r.company_name && <span className="text-sm text-muted">· {r.company_name}</span>}
          </div>

          {r.match_reasons.length > 0 && (
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {r.match_reasons.map((m, i) => (
                <Pill key={i} className="bg-market/10 text-market">{m}</Pill>
              ))}
            </div>
          )}

          {highlights.length > 0 && (
            <div className="mt-2 space-y-1">
              {highlights.slice(0, 2).map(([source, text]) => (
                <p key={source} className="line-clamp-1 text-xs text-muted">
                  <span className="font-mono text-faint">{source}</span> — {text}
                </p>
              ))}
            </div>
          )}
        </div>

        {/* Relevance: number + bar, value always directly labelled. */}
        <div className="shrink-0 text-right">
          <div className="font-display text-lg font-semibold tabular-nums text-heading">
            {Math.round(r.relevance_score * 100)}
          </div>
          <div className="mt-1 h-1.5 w-16 overflow-hidden rounded-full bg-raised">
            <div className="h-full rounded-full bg-accent" style={{ width: `${Math.min(r.relevance_score * 100, 100)}%` }} />
          </div>
          <div className="mt-1 flex items-center justify-end gap-0.5 text-[11px] text-faint">
            profile <ArrowRight className="h-3 w-3" />
          </div>
        </div>
      </button>
    </Card>
  );
}
