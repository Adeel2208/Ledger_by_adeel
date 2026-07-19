# The VC Brain — Project Requirements Document

**Challenge:** #02 — Maschmeyer Group × Hack-Nation, 6th Global AI Hackathon
**Tagline:** Deploying $100K Checks in 24 Hours
**Document purpose:** Single source of truth for scope, features, and user stories to guide the build and keep the team focused on what actually scores points.

---

## 1. Overview

The VC Brain is a data- and AI-first operating system that gives a single investor the reach and analytical power of a full investment team. It covers four pipeline stages — **Sourcing → Screening → Diligence → Decision** — built on three architectural layers: **Memory** (data foundation), **Intelligence** (reasoning/scoring), and **Experience** (investor-facing UX).

**Problem statement:** Capital today flows through networks, not merit. Strong founders — especially first-time, no-network, pre-track-record founders — stay invisible while diligence on the founders who *do* get seen takes weeks. The VC Brain finds founders early (before they start fundraising), scores them consistently and transparently, and gets a $100K investment recommendation to decision-ready status within 24 hours.

**Explicit out-of-scope:** Portfolio monitoring, follow-on investment, fund operations, exit planning. Do not build UI or logic for these.

---

## 2. Objectives & Success Metrics

| Objective | How it's measured |
|---|---|
| Surface strong founders before they fundraise | Outbound sourcing produces at least one activated, previously-invisible founder in the demo |
| Score consistently and transparently | Every opportunity has 3 independent axis scores + a per-claim Trust Score |
| Handle the cold-start case | At least one demoed founder has no funding/GitHub/network history, scored via an explicit alternate method |
| Support a 24-hour decision | End-to-end journey (apply/spot → score → memo → decision) is demonstrable live, start to finish |
| Be trustworthy, not just fast | No fabricated data; every gap explicitly flagged; every claim traceable to a source |

---

## 3. Personas

**Primary user — The Investor (Maschmeyer Group partner)**
A single decision-maker who needs Bloomberg-level analytical depth with Notion-level ease of use. Reviews inbound applications and outbound-sourced leads, sets investment thesis parameters, and makes go/no-go calls on $100K checks.

**Secondary "user" — The Founder**
Either applies directly (deck + company name) or is discovered and activated via outbound outreach. Never sees the investor's internal scoring — only the fact that they were invited to apply or received a decision.

---

## 4. System Architecture

```
┌─────────────────────────────────────────────┐
│ EXPERIENCE LAYER (investor-facing UX)        │
│  Investor dashboard (ranked list + trend)    │
│  Decision-ready outputs (memo + adversarial) │
└─────────────────────────────────────────────┘
                   ▲
┌─────────────────────────────────────────────┐
│ INTELLIGENCE LAYER (reasoning & scoring)     │
│  Thesis Engine · Multi-axis score · Trust    │
│  Score · Multi-Attribute Reasoning           │
└─────────────────────────────────────────────┘
                   ▲
┌─────────────────────────────────────────────┐
│ MEMORY LAYER (data foundation)               │
│  Structured knowledge base · dedup/enrich/   │
│  timestamp · Founder Score (persistent)      │
└─────────────────────────────────────────────┘
```

Pipeline stages map onto these layers as: **Sourcing** (Memory + inbound/outbound ingestion) → **Screening** (Intelligence: 3-axis scoring) → **Diligence** (Intelligence: truth-gap check, Trust Score) → **Decision** (Experience: memo + recommendation).

---

## 5. Functional Requirements

### FR-1 — Thesis Engine
Investor-configurable filter: sectors, stage, geography, check size, ownership targets, risk appetite. Every recommendation is filtered and scored through this lens. Must be configurable at runtime, never hardcoded.

### FR-2 — Smart Data Collection & Management
Ingest founder/company data from multiple heterogeneous sources. Deduplicate, enrich, timestamp, and source-tag every record. Data layer quality is weighted as heavily as the reasoning built on top of it (30% of judging).

### FR-3 — Multi-Attribute Reasoning
Resolve natural-language compound queries (e.g., "technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator") in a single pass — not five manual filters.

### FR-4 — Inbound Application & Screening
Minimum application input: deck + company name. A fast first-pass filter removes clearly non-viable ideas before full analysis runs.

### FR-5 — Outbound Founder Identification & Activation
Continuously scan GitHub, product launches, hackathons, papers/patents, accelerator cohorts. Score discovered founders the same way as inbound applicants. Trigger outreach to convert strong matches into a real application (cold outreach, not cold investment). Activated applications converge into the same screening funnel as inbound.

### FR-6 — Multi-Axis Screening
Score every opportunity on three **independent, non-averaged** axes:
- **Founder** — who they are, traits, track record
- **Market** — sizing, competitors, SWOT (bullish / neutral / bear)
- **Idea vs. Market** — does the idea survive scrutiny as-is, or is the team strong enough to pivot

Each axis also carries a trend direction (improving / declining / stable) and feeds back into Memory to sharpen future scoring.

### FR-7 — Founder Score (persistent)
A cross-application "credit score for founders" that lives in Memory, persists across applications, and never resets. One input into the Founder axis — not a replacement for it. Surfaces trend over time, not just latest snapshot.

### FR-8 — Trust Score & Evidence-Backed Memos
Every claim in a memo (traction, revenue, team background, market size) traces to a specific evidence source with a confidence level. Contradictions between sources are flagged before reaching the investor. Missing data (e.g., cap table, financials) is explicitly disclosed ("Cap table: not disclosed") — never fabricated.

### FR-9 — Investment Memo Generation
Auto-generate a memo containing, at minimum, the five required sections: **Company snapshot, Investment hypotheses, SWOT, Problem & product, Traction & KPIs.** Additional sections (Financials, Cap table, Competition, Exit perspective, Due diligence log) are optional — include only where data exists; flag gaps otherwise. Length rule: as detailed as the decision requires, as brief as clarity allows — padding counts against the score.

### FR-10 — Investor Dashboard
Ranked founder/opportunity list with momentum trend. Usable without technical support (Notion-level approachability, Bloomberg-level analytical depth).

### FR-11 — Cold-Start Handling
An explicit, documented method for scoring founders with no funding history, no GitHub activity, and no network (e.g., public footprint signals, technical artifact quality, direct problem-market-fit reasoning). This is not optional polish — generic ingestion/enrichment that ignores this case scores poorly regardless of other quality.

---

## 6. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Transparency | System must be transparent about confidence, uncertainty, and evidence behind every conclusion — never present a black-box score |
| Honesty over completeness | Never silently fill gaps; always flag missing/unavailable data |
| Consistency | Same scoring logic applies to inbound and outbound-sourced founders — no special-casing |
| Auditability | Every recommendation should be traceable back to source signals (fully required only for the Agentic Traceability stretch goal, but good practice throughout) |
| Usability | Non-technical investor can operate the tool without support |
| Performance | Screening pass should run fast enough to support a same-day (24-hour) decision cycle |

---

## 7. Data Requirements

- **No dataset is provided by organizers.** Bring or synthesize your own.
- Acceptable sources: public web data (Crunchbase, LinkedIn, GitHub, ProductHunt, Hacker News, arXiv, patents), synthetic founder profiles with **seeded contradictions** (to demo Trust Score conflict-flagging), or anonymized/fictional pitch decks.
- **Ingestion quality matters more than dataset size.** A small, clean, well-labeled dataset with clear source tagging beats a large scraped dump.
- Seed set should deliberately include:
  - At least one founder with a strong public track record (GitHub, prior startup, papers)
  - At least one **cold-start founder** with none of the above
  - At least one founder with contradictory signals (e.g., inflated traction claim vs. what's independently verifiable) to demonstrate Trust Score flagging
  - At least one incomplete profile with a genuinely missing data field (to demonstrate honest gap-flagging instead of fabrication)

---

## 8. Suggested Technical Stack

| Layer | Suggestion |
|---|---|
| Storage (Memory layer) | Postgres or SQLite — structured relational schema, not just a vector store (you need dedup/timestamp/source-tag logic) |
| Embeddings/retrieval | Vector store (e.g., pgvector, Chroma) alongside structured storage, for the Multi-Attribute Reasoning queries |
| LLM orchestration | OpenAI API (structured JSON outputs for scores/memos, not free text, so the UI can render them programmatically) |
| Ingestion | GitHub API, arXiv API for real data; synthetic generation for anything requiring private/founder data |
| Backend | Python (FastAPI) or Node — whichever the team ships fastest in |
| Frontend | Streamlit (fastest to build) or a lightweight React dashboard if the team has front-end strength |

---

## 9. User Stories

Organized by epic, in the order they should be built. Each story includes acceptance criteria.

### Epic A — Thesis Engine

**A1.** As an investor, I want to set my investment thesis (sectors, stage, geography, check size, ownership targets, risk appetite), so that every recommendation I see is pre-filtered to what I'd actually invest in.
- *Acceptance:* Thesis is stored and editable; changing it visibly changes the ranked list and scores shown.

**A2.** As an investor, I want the thesis to apply consistently to both inbound applications and outbound-sourced founders, so that I'm comparing opportunities on the same terms.
- *Acceptance:* A founder sourced outbound and one who applied inbound, given identical attributes, receive identical thesis-filtered scores.

### Epic B — Memory / Data Foundation

**B1.** As the system, I need to ingest founder and company signals from multiple sources (GitHub, decks, launches, papers), so that no relevant data point is lost.
- *Acceptance:* Each ingested record is stored with source, timestamp, and type.

**B2.** As the system, I need to deduplicate records referring to the same founder/company across sources, so that the same signal isn't double-counted.
- *Acceptance:* Ingesting the same founder from two sources produces one merged record, not two.

**B3.** As an investor, I want a persistent Founder Score that follows a person across different startups and applications, so that a founder's track record compounds instead of resetting each time.
- *Acceptance:* Founder Score is visible on a founder's profile independent of which company they're currently pitching; applying with a second startup shows the prior score/trend, not a blank slate.

### Epic C — Inbound Sourcing

**C1.** As a founder, I want to apply with just a pitch deck and my company name, so that the barrier to being considered is minimal.
- *Acceptance:* Application form accepts deck + company name as the only required fields; additional fields are optional.

**C2.** As the system, I want to run a fast first-pass filter on new applications, so that clearly non-viable ideas don't consume full analysis resources.
- *Acceptance:* A visibly out-of-thesis or incomplete application is filtered out with a stated reason before reaching full scoring.

### Epic D — Outbound Sourcing

**D1.** As the system, I want to continuously scan GitHub, hackathon results, papers/patents, and accelerator cohorts, so that I can surface strong founders before they start fundraising.
- *Acceptance:* At least one demo founder is discovered via outbound scan, not inbound application.

**D2.** As the system, I want to score outbound-discovered founders using the same method as inbound applicants, so that sourcing channel doesn't bias the evaluation.
- *Acceptance:* Outbound and inbound founders with equivalent attributes produce equivalent scores.

**D3.** As the system, I want to trigger outreach to strong outbound matches to invite them to apply, so that discovery converts into a real, actionable pipeline rather than a passive watchlist.
- *Acceptance:* A discovered founder has a demonstrable "activate" action that converts them into the same application/screening flow as inbound.

### Epic E — Multi-Axis Screening

**E1.** As an investor, I want each opportunity scored independently on Founder, Market, and Idea-vs-Market axes, so that I can see exactly where the strength or weakness lies rather than one blended number hiding disagreement.
- *Acceptance:* All three axis scores are displayed separately, never averaged into a single figure.

**E2.** As an investor, I want each axis to show a trend direction (improving/declining/stable), so that I understand momentum, not just a snapshot.
- *Acceptance:* Each axis has a visible trend indicator tied to at least two data points over time (even if simulated for demo purposes).

**E3.** As an investor evaluating a first-time founder with no GitHub, no funding, and no network, I want the system to score them using an explicit alternate method rather than defaulting to a low/no score, so that promising cold-start founders aren't filtered out by a system that just reproduces the network-gated status quo.
- *Acceptance:* At least one demoed cold-start founder receives a substantive Founder-axis score with a documented rationale distinct from the track-record-based method used for established founders.

### Epic F — Diligence / Trust

**F1.** As an investor, I want every factual claim in a memo (traction, revenue, team background, market size) to link back to its source evidence with a confidence level, so that I can judge how much to trust each claim.
- *Acceptance:* Clicking/inspecting any claim in the memo shows its source and a confidence tag.

**F2.** As an investor, I want contradictions between sources to be flagged automatically, so that I catch inflated or inconsistent claims before they influence my decision.
- *Acceptance:* A seeded contradiction in the demo dataset (e.g., a claimed metric that conflicts with an independent source) is visibly flagged in the memo, not silently resolved.

**F3.** As an investor, I want missing data explicitly labeled as missing (e.g., "Cap table: not disclosed") rather than guessed or fabricated, so that I can trust the memo's completeness claims.
- *Acceptance:* At least one demoed memo has a genuinely absent data field, shown as an explicit flag, not omitted silently or filled with a plausible-looking guess.

### Epic G — Decision / Memo

**G1.** As an investor, I want an auto-generated investment memo covering Company snapshot, Investment hypotheses, SWOT, Problem & product, and Traction & KPIs, so that I have a decision-ready document without manual write-up.
- *Acceptance:* Memo output contains all five required sections, populated from ingested/scored data.

**G2.** As an investor, I want the memo to be concise rather than padded, so that I can act on it quickly.
- *Acceptance:* Memo length scales with available evidence; sections with no data are flagged briefly, not padded with generic text.

**G3.** As an investor, I want to see an adversarial/risk view alongside the positive case, so that I'm not only shown a one-sided pitch.
- *Acceptance:* Memo or dashboard surfaces at least one explicit risk/weakness per opportunity, not just strengths.

### Epic H — Investor Dashboard (Experience Layer)

**H1.** As an investor, I want a ranked list of opportunities with momentum trend, so that I can quickly triage where to focus.
- *Acceptance:* Dashboard shows opportunities ranked by thesis-fit/score, each with a visible trend indicator.

**H2.** As a non-technical investor, I want the interface to be usable without training, so that I can adopt it into my actual workflow.
- *Acceptance:* A first-time user can navigate from dashboard → memo → decision without external explanation.

### Epic I — Stretch Goals (build only after Epics A–H are solid)

**I1 (highest priority stretch).** As an investor, I want every recommendation to cite the exact data point (deck slide, web signal, interview excerpt) that drove it, so that I can verify the system's reasoning myself.
- *Acceptance:* At least one memo conclusion links to a specific, inspectable source artifact, with step-level reasoning visible.

**I2.** As the system, I want a Validator Agent that cross-references founder claims against external market data, so that the primary scoring agent's outputs are checked rather than trusted blindly.
- *Acceptance:* A seeded false/exaggerated claim is caught and flagged by the validator in the demo.

**I3.** As an investor, I want the system to track which sourcing channels historically produce the strongest opportunities and suggest underexplored ones, so that sourcing improves over time rather than staying static.
- *Acceptance:* A simple channel-performance view exists, even if seeded with limited historical data for the demo.

---

## 10. End-to-End Demo Script (what judges should see)

1. Set/show the investor's Thesis Engine configuration.
2. Show an **inbound** application (deck + company name) pass through first-pass screening.
3. Show an **outbound**-sourced founder (e.g., discovered via GitHub) get activated and converge into the same funnel.
4. Show both founders scored on the three independent axes with trend direction — including **one cold-start founder** scored via the documented alternate method.
5. Open a generated memo: required sections populated, at least one claim traced to its evidence, at least one contradiction flagged, at least one gap explicitly disclosed (not fabricated).
6. Show the ranked dashboard view.
7. (If time allows) Show Agentic Traceability — click a memo conclusion and see the exact source artifact behind it.

---

## 11. Judging Criteria Mapping (build priority should follow this weighting)

| Criterion | Weight | Primary epics covering it |
|---|---|---|
| Data Architecture and Intelligence | 30% | B (Memory), D (Outbound), E3 (Cold-start) |
| Investment Utility & Execution | 30% | C, D, G (Decision-ready memo, 24hr usability) |
| Intelligent Analysis and Trust | 25% | E, F (Multi-axis scoring, Trust Score) |
| User Experience and Design | 15% | H (Dashboard) |

**Build order should follow weight, not visual appeal.** Sourcing/data + cold-start handling (30%) and decision utility (30%) come before dashboard polish (15%).

---

## 12. Explicit Non-Negotiables (any violation caps your score regardless of quality elsewhere)

- Never average the three screening axes into a single number.
- Never fabricate missing data — flag it explicitly.
- Never build UI/logic for portfolio monitoring, follow-on, fund ops, or exit — out of scope.
- Never let the Founder Score reset between applications — it is persistent by design.
- Don't over-collect application fields — deck + company name is the bar; additional fields must be justified by the 24-hour decision need.

---

## 13. Risks & Open Questions to Resolve Early

- **Cold-start scoring method** — decide and document this before building anything else in Epic E; it's the single most-flagged differentiator in the brief.
- **Data source availability** — confirm which of GitHub/arXiv/etc. APIs are reachable in the hackathon environment before committing to them; have a synthetic-data fallback ready.
- **Time budget** — Memory + Screening (Epics B–E) should consume the majority of hours; leave explicit buffer for the demo script rehearsal (Section 10) rather than cutting it for extra features.
