# Cold-Start Founder Scoring Method

> **Requirements FR-11 / Epic E3.** The single most-flagged differentiator in the brief.
> Decide and document this *before* building Epic E. Generic ingestion that ignores this
> case scores poorly regardless of other quality.

## The problem

Traditional VC scoring keys off track-record signals — prior exits, funding history, GitHub
star counts, warm-intro network. A first-time founder with none of these isn't *weak*; they're
*invisible to the signal set*. A naive system defaults them to a low/no score and thereby
reproduces the exact network-gated status quo the VC Brain exists to break.

**Rule:** the system must NEVER default a cold-start founder to a low score for *absence* of
track-record signals. Absence of evidence is flagged as a gap, not scored as a negative.

## Detection

A founder is flagged `is_cold_start = true` when they lack **all** of:
funding history, meaningful GitHub activity, and an established network — i.e. the
track-record scorer has near-zero signal to work with.

## Alternate signal set (what we score *instead*)

| Signal family | Concrete sources | What it proxies |
|---|---|---|
| **Technical-artifact quality** | side-project repos, portfolio site, deployed demo, code samples | execution ability, craft |
| **Public footprint** | blog posts, technical write-ups, YouTube, conference talks | communication, depth of thought |
| **Community contribution** | Stack Overflow, open-source issues/PRs, Discord/forum help | collaboration, domain immersion |
| **Self-directed learning** | courses, certifications, self-taught trajectory | resilience, drive |
| **Participation (not just wins)** | hackathon entries, accelerator applications, side ventures | initiative, bias to action |
| **Direct problem–market-fit reasoning** | the deck + a lived-experience narrative | insight quality, founder-market fit |

## Scoring approach

The cold-start scorer (`intelligence/scoring/cold_start.py`) produces a **substantive
Founder-axis score with an explicit, distinct rationale** — not a discounted version of the
track-record score. Two rules keep it fair and honest:

1. **Alternate signals are weighted equal to traditional ones**, not as a consolation tier.
   A strong deployed demo can carry as much weight as a GitHub history would have.
2. **The rationale states the method used** ("scored via cold-start method: technical-artifact
   quality + problem–market-fit reasoning, no track-record data available"), so the investor
   sees *why* and *how*, never a black-box number (NFR: Transparency).

## Bias guard

Cold-start handling is also a bias-mitigation mechanism: underrepresented founders are
disproportionately network-poor. The scorer must be audited to ensure it does not penalize
missing traditional signals — only reward present alternate ones.

## Demo acceptance (Epic E3)

At least one demoed founder has **no** funding/GitHub/network history and receives a
substantive Founder-axis score with a documented rationale distinct from the track-record path.
Seed this founder in `scripts/seed_data.py`.
