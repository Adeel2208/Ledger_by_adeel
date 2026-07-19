# Data Model

Founder-centric (not company-centric) so the persistent Founder Score has a stable root that
outlives any single venture (FR-7).

```
Founder ──1:N── Application ──N:1── Company
   │                 │
   │                 ├──1:N── AxisScore   (axis ∈ {founder, market, idea}; many rows → trend)
   │                 └──1:1── Memo ──1:N── MemoSection ──1:N── Claim ──1:N── Evidence ──N:1── Signal
   │
   ├──1:N── Signal        (source, timestamp, confidence, record_type, payload)  ← Memory truth
   └──1:N── FounderScore  (persistent, versioned history — never reset)

Thesis (versioned)        Outreach (founder, channel, status: discovered→contacted→activated)
```

## Entities

| Table | Purpose | Key invariant |
|---|---|---|
| `founders` | Stable root person | `is_cold_start` flag drives alternate scoring |
| `companies` | A venture (many per founder over time) | — |
| `applications` | One founder × one company in the pipeline | `channel` recorded but never scored on |
| `signals` | Raw ingested evidence points | ALWAYS has source + timestamp + confidence + record_type |
| `axis_scores` | The three independent axis scores over time | never averaged; `axis` is one of three |
| `founder_scores` | Persistent cross-application score history | never reset between applications |
| `memos` / `memo_sections` / `claims` | Decision-ready output | `is_gap` marks explicit missing-data flags |
| `evidence` | Claim → Signal link with confidence tier | a "verified" claim must have ≥1 row here |
| `theses` | Runtime-configurable investment thesis | versioned; `is_active` selects current |
| `outreach` | Outbound activation tracking | status converges into inbound funnel |

## Provenance & honesty (design-enforced)

- **Every `Signal`** records where it came from, when, and how much to trust it. Dedup merges
  records but preserves provenance (audit trail) — it never deletes source signals.
- **Evidence is a table, not a prompt.** The link between a memo claim and its backing signal
  is structural, so "no evidence ⇒ cannot be verified" is a schema guarantee, not a hope.
- **Gaps are rows too.** A missing field becomes a `MemoSection` with `is_gap = true`, so the
  memo can *show* the gap rather than omit or fabricate it (FR-8 / F3).

## Dev vs. prod

Identical ORM on both. Dev = SQLite + Chroma. Prod = Postgres + pgvector (and TimescaleDB for
score history if score-volume grows). Swapping is a `DATABASE_URL` / `VECTOR_BACKEND` change.
