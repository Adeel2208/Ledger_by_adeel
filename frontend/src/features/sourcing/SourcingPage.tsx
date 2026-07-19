import { useActivate, useDiscovered, useScan, type Discovered } from "@/api/hooks";
import { TrendArrow } from "@/components/scores/ScoreViz";
import { Card, EmptyState, Pill, SectionLabel, Spinner } from "@/components/ui/primitives";
import { Github, Radar, Rocket } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SourcingPage() {
  const { data: discovered, isLoading } = useDiscovered();
  const scan = useScan();
  const [username, setUsername] = useState("");

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-heading">Outbound Sourcing</h1>
        <p className="mt-0.5 text-sm text-muted">
          Find strong founders before they fundraise. Discovered founders are scored the same
          way as inbound applicants — then activated into the same funnel.
        </p>
      </header>

      {/* Scan */}
      <Card className="p-5">
        <SectionLabel>Scan a source</SectionLabel>
        <div className="mt-3 flex items-center gap-3">
          <div className="relative flex-1">
            <Github className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-faint" />
            <input
              className="input w-full pl-9"
              placeholder="GitHub username, e.g. torvalds"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && username && scan.mutate({ source: "github", params: { username } })}
            />
          </div>
          <button
            className="btn-primary"
            disabled={!username || scan.isPending}
            onClick={() => scan.mutate({ source: "github", params: { username } })}
          >
            {scan.isPending ? <Spinner className="h-4 w-4" /> : <Radar className="h-4 w-4" />}
            Scan
          </button>
        </div>
        {scan.isError && <div className="mt-2 text-xs text-danger">{String(scan.error)}</div>}
        {scan.isSuccess && (
          <div className="mt-2 text-xs text-success">
            Ingested {String((scan.data as { signals_added?: number }).signals_added ?? 0)} signals —
            founder added to the watchlist below.
          </div>
        )}
      </Card>

      {/* Watchlist */}
      <div>
        <SectionLabel>Discovered — awaiting activation</SectionLabel>
        <div className="mt-3 space-y-3">
          {isLoading ? (
            <div className="flex justify-center py-10"><Spinner className="h-5 w-5 text-muted" /></div>
          ) : !discovered?.length ? (
            <EmptyState title="No discovered founders" hint="Run a scan above to surface someone." />
          ) : (
            discovered.map((d) => <DiscoveredRow key={d.founder_id} d={d} />)
          )}
        </div>
      </div>
    </div>
  );
}

function DiscoveredRow({ d }: { d: Discovered }) {
  const activate = useActivate();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [sector, setSector] = useState("");

  return (
    <Card className="p-4">
      <div className="flex items-center gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{d.name}</span>
            {d.github_handle && (
              <a
                href={`https://github.com/${d.github_handle}`}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-muted hover:text-ink"
              >
                @{d.github_handle}
              </a>
            )}
            <Pill className="bg-raised text-faint">{d.signal_count} signals</Pill>
          </div>
          <div className="mt-0.5 flex items-center gap-1.5 text-sm text-muted">
            Founder Score{" "}
            <span className="font-semibold tabular-nums text-ink">{d.founder_score ?? "—"}</span>
            {d.momentum && <TrendArrow trend={d.momentum as never} />}
          </div>
        </div>
        <button className="btn-primary text-xs" onClick={() => setOpen((v) => !v)}>
          <Rocket className="h-3.5 w-3.5" /> Activate
        </button>
      </div>

      {open && (
        <div className="mt-4 flex items-end gap-3 border-t border-border pt-4">
          <div className="flex-1">
            <SectionLabel>Company name</SectionLabel>
            <input className="input mt-1 w-full" placeholder="What are they building?"
                   value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
          </div>
          <div className="w-40">
            <SectionLabel>Sector</SectionLabel>
            <input className="input mt-1 w-full" placeholder="e.g. AI"
                   value={sector} onChange={(e) => setSector(e.target.value)} />
          </div>
          <button
            className="btn-primary text-xs"
            disabled={!companyName || activate.isPending}
            onClick={() =>
              activate.mutate(
                { founderId: d.founder_id, company_name: companyName, sector: sector || undefined },
                { onSuccess: () => navigate("/dashboard") },
              )
            }
          >
            {activate.isPending ? <Spinner className="h-3.5 w-3.5" /> : null}
            Invite to apply → funnel
          </button>
        </div>
      )}
    </Card>
  );
}
