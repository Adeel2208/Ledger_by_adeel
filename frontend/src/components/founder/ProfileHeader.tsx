import type { FounderDetail } from "@/api/types";
import { Avatar } from "@/components/founder/Avatar";
import { TrendArrow } from "@/components/scores/ScoreViz";
import { Card, Pill } from "@/components/ui/primitives";
import { Brain, Github, Globe, Linkedin, MapPin, Snowflake, Twitter } from "lucide-react";
import type { ComponentType } from "react";
import { Link } from "react-router-dom";

/** Human labels for profile facets the founder has not supplied yet. */
const FACET_LABELS: Record<string, string> = {
  photo_path: "photo",
  headline: "headline",
  bio: "bio",
  role: "role",
  location: "location",
  work_history: "work history",
};

export function ProfileHeader({ f }: { f: FounderDetail }) {
  const p = f.profile;

  return (
    <Card className="overflow-hidden">
      {/* Brand band gives the dossier a masthead rather than a bare row. */}
      <div className="h-24 bg-brand" />

      <div className="px-6 pb-6">
        {/* Overlap the band by half the avatar so it straddles the edge; the
            text column sits below the band, not on top of it. */}
        <div className="-mt-12 flex flex-wrap items-start gap-5">
          <Avatar profile={p} name={f.name} size="xl" className="ring-surface" />
          {/* pt-12 pushes the name clear of the band the avatar overlaps. */}
          <div className="min-w-0 flex-1 pt-12">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="font-display text-2xl font-semibold text-heading">{f.name}</h1>
              {f.is_cold_start && (
                <Pill className="bg-market/15 text-market">
                  <Snowflake className="h-3 w-3" /> Cold-start · alternate scoring
                </Pill>
              )}
            </div>

            {p.headline ? (
              <p className="mt-1 text-sm text-ink">{p.headline}</p>
            ) : (
              p.role && <p className="mt-1 text-sm text-ink">{p.role}</p>
            )}

            <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted">
              {p.location && (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5" /> {p.location}
                </span>
              )}
              <ProfileLink icon={Github} href={f.github_handle ? `https://github.com/${f.github_handle}` : null} label={f.github_handle} />
              <ProfileLink icon={Linkedin} href={p.linkedin_url} label="LinkedIn" />
              <ProfileLink icon={Twitter} href={p.twitter_handle ? `https://x.com/${p.twitter_handle}` : null} label={p.twitter_handle} />
              <ProfileLink icon={Globe} href={p.personal_url} label="Website" />
            </div>
          </div>

          {/* Score sits in the masthead so the headline number reads with the person. */}
          <div className="shrink-0 pt-12 text-right">
            <div className="text-[11px] uppercase tracking-wide text-faint">Founder Score</div>
            <div className="flex items-center justify-end gap-2">
              <span className="font-display text-3xl font-semibold tabular-nums text-heading">
                {f.founder_score ?? "—"}
              </span>
              {f.momentum && <TrendArrow trend={f.momentum} />}
            </div>
            <div className="text-[11px] text-faint">never resets</div>
            <Link
              to={`/founders/${f.id}/intelligence`}
              className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
            >
              <Brain className="h-3.5 w-3.5" /> Intelligence
            </Link>
          </div>
        </div>

        {p.bio && <p className="mt-5 max-w-3xl text-sm leading-relaxed text-ink">{p.bio}</p>}

        {/* Missing facets are disclosed, never silently blank — the same
            honesty rule the signal layer follows. */}
        {p.completeness.missing.length > 0 && (
          <p className="mt-4 text-[11px] text-faint">
            Profile {p.completeness.pct}% complete · not supplied:{" "}
            {p.completeness.missing.map((m) => FACET_LABELS[m] ?? m).join(", ")}
          </p>
        )}
      </div>
    </Card>
  );
}

function ProfileLink({
  icon: Icon,
  href,
  label,
}: {
  icon: ComponentType<{ className?: string }>;
  href: string | null;
  label: string | null;
}) {
  if (!href) return null;
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1 hover:text-accent"
    >
      <Icon className="h-3.5 w-3.5" /> {label ?? href}
    </a>
  );
}
