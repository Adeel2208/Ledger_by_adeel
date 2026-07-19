import { useApply } from "@/api/hooks";
import { Card, Pill, SectionLabel, Spinner } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import { CheckCircle2, FileUp, Image as ImageIcon, Send, XCircle, CircleDot } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";

const DECISION_META: Record<string, { icon: typeof CheckCircle2; cls: string; label: string }> = {
  pass: { icon: CheckCircle2, cls: "text-success", label: "Passed first-pass screening" },
  review: { icon: CircleDot, cls: "text-claimed", label: "Routed to human review" },
  fail: { icon: XCircle, cls: "text-danger", label: "Not a fit right now" },
};

export default function ApplyPage() {
  const apply = useApply();
  const fileRef = useRef<HTMLInputElement>(null);
  const [companyName, setCompanyName] = useState("");
  const [fileName, setFileName] = useState<string | null>(null);
  const [founderName, setFounderName] = useState("");
  const [founderEmail, setFounderEmail] = useState("");

  // Optional founder profile. Kept behind a disclosure so the headline promise
  // — deck + company name — stays true.
  const photoRef = useRef<HTMLInputElement>(null);
  const [showProfile, setShowProfile] = useState(false);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [profile, setProfile] = useState({
    headline: "",
    role: "",
    location: "",
    linkedin: "",
    bio: "",
  });

  const onPhotoPick = () => {
    const file = photoRef.current?.files?.[0];
    setPhotoPreview(file ? URL.createObjectURL(file) : null);
  };

  const submit = () => {
    const form = new FormData();
    form.set("company_name", companyName);
    const file = fileRef.current?.files?.[0];
    if (file) form.set("deck", file);
    if (founderName) form.set("founder_name", founderName);
    if (founderEmail) form.set("founder_email", founderEmail);

    const photo = photoRef.current?.files?.[0];
    if (photo) form.set("founder_photo", photo);
    if (profile.headline) form.set("founder_headline", profile.headline);
    if (profile.role) form.set("founder_role", profile.role);
    if (profile.location) form.set("founder_location", profile.location);
    if (profile.linkedin) form.set("founder_linkedin", profile.linkedin);
    if (profile.bio) form.set("founder_bio", profile.bio);

    apply.mutate(form);
  };

  const result = apply.data;
  const decision = result ? DECISION_META[result.screening.decision] : null;

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-heading">Apply for a $100K check</h1>
        <p className="mt-0.5 text-sm text-muted">
          Deck + company name. That's the whole application — a decision-ready evaluation
          within 24 hours.
        </p>
      </header>

      {result && decision ? (
        <Card className="space-y-4 p-6">
          <div className="flex items-center gap-3">
            <decision.icon className={cn("h-8 w-8", decision.cls)} />
            <div>
              <div className="font-semibold">{decision.label}</div>
              <div className="text-sm text-muted">{result.screening.reason}</div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <Pill className="bg-raised text-muted">thesis fit {result.screening.thesis_fit}/100</Pill>
            <Pill className="bg-raised text-muted">{result.signals_extracted} signals extracted</Pill>
          </div>
          {result.warnings.length > 0 && (
            <div className="text-xs text-claimed">{result.warnings.join(" ")}</div>
          )}
          <div className="flex gap-3 border-t border-border pt-4">
            <Link to="/dashboard" className="btn-primary text-xs">View in Deal Flow</Link>
            <button className="btn-ghost text-xs" onClick={() => apply.reset()}>
              Submit another
            </button>
          </div>
        </Card>
      ) : (
        <Card className="space-y-5 p-6">
          <div>
            <SectionLabel>Company name *</SectionLabel>
            <input
              className="input mt-1.5 w-full"
              placeholder="e.g. InferGrid"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
            />
          </div>

          <div>
            <SectionLabel>Pitch deck * (PDF / PPTX / DOCX)</SectionLabel>
            <button
              className={cn(
                "mt-1.5 flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-sm transition-colors",
                fileName ? "border-accent/40 text-ink" : "border-border text-muted hover:border-accent/40",
              )}
              onClick={() => fileRef.current?.click()}
            >
              <FileUp className="h-4 w-4" />
              {fileName ?? "Choose your deck"}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.pptx,.docx"
              className="hidden"
              onChange={(e) => setFileName(e.target.files?.[0]?.name ?? null)}
            />
          </div>

          <details className="text-sm">
            <summary className="cursor-pointer text-xs text-faint">
              Optional: founder name & email (helps us match your track record)
            </summary>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <input className="input" placeholder="Founder name"
                     value={founderName} onChange={(e) => setFounderName(e.target.value)} />
              <input className="input" placeholder="Email"
                     value={founderEmail} onChange={(e) => setFounderEmail(e.target.value)} />
            </div>
          </details>

          <details className="text-sm" open={showProfile}
                   onToggle={(e) => setShowProfile((e.target as HTMLDetailsElement).open)}>
            <summary className="cursor-pointer text-xs text-faint">
              Optional: your profile — photo, role & background
            </summary>
            <div className="mt-3 space-y-3">
              <div className="flex items-center gap-3">
                {photoPreview ? (
                  <img src={photoPreview} alt="" className="h-14 w-14 rounded-full object-cover ring-1 ring-border" />
                ) : (
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-raised">
                    <ImageIcon className="h-5 w-5 text-faint" />
                  </div>
                )}
                <div>
                  <button type="button" className="btn-ghost text-xs" onClick={() => photoRef.current?.click()}>
                    {photoPreview ? "Change photo" : "Add a photo"}
                  </button>
                  <p className="mt-1 text-[11px] text-faint">JPEG, PNG or WebP · up to 5MB</p>
                </div>
                <input ref={photoRef} type="file" accept="image/jpeg,image/png,image/webp"
                       className="hidden" onChange={onPhotoPick} />
              </div>

              <input className="input w-full" placeholder="Headline — e.g. Founder & CTO, Acme"
                     value={profile.headline}
                     onChange={(e) => setProfile({ ...profile, headline: e.target.value })} />
              <div className="grid grid-cols-2 gap-3">
                <input className="input" placeholder="Role"
                       value={profile.role}
                       onChange={(e) => setProfile({ ...profile, role: e.target.value })} />
                <input className="input" placeholder="Location"
                       value={profile.location}
                       onChange={(e) => setProfile({ ...profile, location: e.target.value })} />
              </div>
              <input className="input w-full" placeholder="LinkedIn URL"
                     value={profile.linkedin}
                     onChange={(e) => setProfile({ ...profile, linkedin: e.target.value })} />
              <textarea className="input w-full" rows={3} placeholder="Short bio"
                        value={profile.bio}
                        onChange={(e) => setProfile({ ...profile, bio: e.target.value })} />
            </div>
          </details>

          {apply.isError && (
            <div className="text-xs text-danger">{String(apply.error)}</div>
          )}

          <button
            className="btn-primary w-full"
            disabled={!companyName || !fileName || apply.isPending}
            onClick={submit}
          >
            {apply.isPending ? <Spinner className="h-4 w-4" /> : <Send className="h-4 w-4" />}
            {apply.isPending ? "Parsing deck & screening…" : "Submit application"}
          </button>
          <p className="text-center text-[11px] text-faint">
            We never ask for more than the decision needs.
          </p>
        </Card>
      )}
    </div>
  );
}
