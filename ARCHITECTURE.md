# The VC Brain — Architecture

**Status:** v1 (scaffold) · **Owner:** Dev Team · **Last updated:** 2026-07-19

This document is the source of truth for *how the system is built*. Scope and features live in
[VC_Brain_Requirements.md](VC_Brain_Requirements.md); the long-term enterprise vision lives in
[PROJECT_PLAN.md](PROJECT_PLAN.md).

---

## 1. Design principles

1. **Modular monolith, not microservices.** One deployable FastAPI app whose *modules* map 1:1 to
   the three layers. This ships in a hackathon timebox yet each module has a clean seam, so any of
   them can be extracted into its own service later without a rewrite.
2. **Layer boundaries are enforced by dependency direction.** `Experience → Intelligence → Memory`.
   Lower layers never import from higher ones. Cross-layer orchestration lives in `services/`.
3. **The data layer is a first-class citizen** (30% of judging). Every signal is stored relationally
   with `source`, `timestamp`, `confidence`, and `record_type`. Vectors are an *index over* that
   truth, never the source of truth.
4. **Everything the LLM produces is structured JSON**, validated by Pydantic, so the UI renders it
   programmatically and we can unit-test scores/memos.
5. **Provider-agnostic AI.** All model calls go through `app/llm`. Swapping OpenAI ↔ Anthropic is a
   config change, not a code change.
6. **Honesty by construction.** Trust/evidence is a data model concern (the `Evidence` table), not a
   prompt afterthought. A claim with no linked evidence *cannot* be marked verified.

---

## 2. High-level architecture

```
                        ┌──────────────────────────────────────┐
                        │            FRONTEND (React)           │
                        │  Dashboard · Memo · Thesis · Sourcing │
                        └───────────────────┬──────────────────┘
                                            │ REST (JSON) / SSE
┌───────────────────────────────────────────┴───────────────────────────────────────────┐
│                                   BACKEND (FastAPI)                                      │
│                                                                                         │
│   app/api  ──────────  EXPERIENCE LAYER (HTTP surface: routers, DTOs, SSE)              │
│      │                                                                                  │
│      ▼                                                                                  │
│   app/services  ─────  ORCHESTRATION (pipeline: Sourcing→Screening→Diligence→Decision)  │
│      │                                                                                  │
│      ▼                                                                                  │
│   app/intelligence  ─  INTELLIGENCE LAYER                                               │
│      │   thesis_engine · screening · scoring/{founder,market,idea,cold_start,trend}     │
│      │   trust/{evidence_tracer,contradiction,validator_agent} · reasoning · retrieval  │
│      ▼                                                                                  │
│   app/memory  ───────  MEMORY LAYER                                                     │
│      │   ingestion/{deck,github,arxiv,producthunt,web} · dedup · enrichment             │
│      │   founder_score (persistent) · repository                                        │
│      ▼                                                                                  │
│   app/models + app/database  ──  PERSISTENCE (SQLAlchemy ORM)                           │
│                                                                                         │
│   app/llm  ──────────  CROSS-CUTTING: provider-agnostic LLM + embeddings               │
│   app/core ──────────  CROSS-CUTTING: config, logging, security, exceptions, events    │
│   app/workers ───────  BACKGROUND: outbound scan scheduler, async ingestion jobs        │
└──────────────────────────────┬─────────────────────────────┬──────────────────────────┘
                               │                             │
                     ┌─────────▼─────────┐         ┌─────────▼─────────┐
                     │  Relational store │         │   Vector index    │
                     │ SQLite / Postgres │         │ Chroma / pgvector │
                     └───────────────────┘         └───────────────────┘
```

**Dependency rule:** an arrow means "may import from". Memory knows nothing about Intelligence;
Intelligence knows nothing about the API. Services wire them together.

---

## 3. Module responsibilities

### 3.1 Memory layer — `app/memory/`  *(Requirements FR-2, FR-7 · Epic B · 30% weight)*

| File | Responsibility |
|---|---|
| `ingestion/base.py` | `BaseConnector` interface — every source implements `fetch() -> list[Signal]` |
| `ingestion/deck_parser.py` | PDF/PPTX/DOCX → structured claims (with OCR fallback) |
| `ingestion/github.py` | GitHub API → contribution/quality signals |
| `ingestion/arxiv.py` | arXiv API → research-paper signals |
| `ingestion/producthunt.py` | Product launch signals |
| `ingestion/web.py` | Generic web / public-footprint scraper (rate-limited, ethical) |
| `ingestion/registry.py` | Maps source name → connector; drives outbound scan |
| `dedup.py` | Entity resolution: fuzzy name/email/handle matching → merge into one founder |
| `enrichment.py` | Fill/attach public-source enrichment; tag reliability |
| `founder_score.py` | **Persistent Founder Score** engine — cross-application, never resets, momentum-aware |
| `repository.py` | All DB reads/writes for the Memory layer (repository pattern) |

**Key rule:** every stored `Signal` carries `{source, timestamp, confidence, record_type}`. Dedup
merges *records*, never destroys provenance (audit trail preserved).

### 3.2 Intelligence layer — `app/intelligence/`  *(FR-1,3,6,8 · Epics A,E,F · 25% weight)*

| File | Responsibility |
|---|---|
| `thesis_engine.py` | Runtime-configurable thesis (sector/stage/geo/check/ownership/risk); scores fit 0–100. **Applied identically to inbound & outbound.** |
| `screening.py` | Fast first-pass filter — cheap pass/fail with stated reason before full analysis |
| `scoring/base.py` | `BaseAxisScorer` — common contract for the three axes |
| `scoring/founder_axis.py` | Founder axis (traits, track record) — pulls persistent Founder Score as *one input* |
| `scoring/market_axis.py` | Market axis (TAM/competitors/SWOT → bullish/neutral/bear) |
| `scoring/idea_axis.py` | Idea-vs-Market axis (does it survive scrutiny / can the team pivot) |
| `scoring/cold_start.py` | **Documented alternate scoring** for no-GitHub/no-funding/no-network founders → [docs/COLD_START.md](docs/COLD_START.md) |
| `scoring/trend.py` | Trend direction per axis from ≥2 historical score points |
| `trust/evidence_tracer.py` | Links each memo claim → `Evidence` rows with confidence tier |
| `trust/contradiction.py` | Cross-source contradiction detection → flags |
| `trust/validator_agent.py` | *(Stretch I2)* second agent that cross-checks claims vs external data |
| `reasoning.py` | NL compound-query understanding → structured query (FR-3) |
| `retrieval.py` | Vector search over signals (provider-abstracted: Chroma/pgvector) |

**Non-negotiable enforced here:** the three axes are returned as a `TripleScore` object; there is
**no code path that averages them**. See [docs/SCORING.md](docs/SCORING.md).

### 3.3 Experience layer — `app/api/` + `frontend/`  *(FR-9,10 · Epics G,H · 15% weight)*

Backend routers under `app/api/v1/` expose the surface; the React app consumes it.

| Router | Endpoints (illustrative) |
|---|---|
| `thesis.py` | `GET/PUT /thesis` |
| `applications.py` | `POST /applications` (deck + company name only), `GET /applications/{id}` |
| `founders.py` | `GET /founders`, `GET /founders/{id}` (persistent score + history) |
| `sourcing.py` | `POST /sourcing/scan`, `POST /sourcing/{id}/activate` (outbound→funnel) |
| `scores.py` | `GET /opportunities/{id}/scores` (triple axis + trend) |
| `memos.py` | `POST /opportunities/{id}/memo`, `GET /memos/{id}` (with inline evidence) |
| `search.py` | `POST /search` (NL multi-attribute query) |
| `dashboard.py` | `GET /dashboard` (ranked list + momentum), SSE stream |

### 3.4 Orchestration — `app/services/`

Services own the *pipeline*, coordinating layers so routers stay thin and layers stay decoupled.

- `pipeline.py` — the Sourcing→Screening→Diligence→Decision state machine.
- `sourcing_service.py` · `screening_service.py` · `diligence_service.py` · `memo_service.py` · `outreach_service.py`.

### 3.5 Cross-cutting

- **`app/llm/`** — `base.LLMProvider` interface; `openai_provider.py`, `anthropic_provider.py`,
  `embeddings.py`, versioned `prompts/`, `client.py` factory. Structured-output helper enforces a
  Pydantic schema on every completion.
- **`app/core/`** — `config` (pydantic-settings), `logging`, `security` (auth/RBAC), `exceptions`,
  `events` (lightweight in-process event bus so Memory can emit "signal ingested" without importing
  Intelligence).
- **`app/workers/`** — `scheduler.py` (APScheduler) runs the outbound scan on an interval;
  `tasks.py` wraps long ingestion as background tasks. Seam is queue-shaped, so Celery/Bull can drop
  in later without touching callers.

---

## 4. Data model (core entities)

```
Founder ──1:N── Application ──N:1── Company
   │                 │
   │                 ├──1:N── AxisScore   (axis ∈ {founder, market, idea}, value, trend, ts)
   │                 └──1:1── Memo ──1:N── MemoSection ──1:N── Claim ──N:M── Evidence
   │
   ├──1:N── Signal   (source, timestamp, confidence, record_type, payload)   ← Memory truth
   └──1:1── FounderScore  (persistent, versioned history)                    ← never resets

Thesis (singleton-ish, versioned)   Outreach (founder, channel, status)
```

Full schema & rationale: [docs/DATA_MODEL.md](docs/DATA_MODEL.md).

**Why founder-centric (not company-centric):** the persistent Founder Score (FR-7) requires the
Founder to be the stable root entity that outlives any single Company/Application.

---

## 5. The pipeline (end-to-end)

```
 SOURCING                     SCREENING              DILIGENCE                 DECISION
─────────────              ───────────────       ────────────────         ────────────────
inbound: POST /applications
   deck + company name  ─┐
                         ├─► thesis fit + ──► 3-axis scoring ──► evidence trace + ──► memo + adversarial
outbound: scan → activate │   fast filter      (never averaged)    contradiction /       view + recommendation
   (same funnel)        ─┘   (pass/fail +       + trend            gap flagging          → dashboard rank
                              reason)            + cold-start
```

Inbound and outbound **converge before screening**, guaranteeing identical treatment (FR-5, D2).

---

## 6. Environment & configuration

All config via env (`app/core/config.py`, `pydantic-settings`). See [`backend/.env.example`](backend/.env.example).

| Var | Purpose |
|---|---|
| `LLM_PROVIDER` | `openai` \| `anthropic` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | model access |
| `LLM_MODEL` / `EMBEDDING_MODEL` | model IDs |
| `DATABASE_URL` | `sqlite:///./vcbrain.db` (dev) or Postgres DSN (prod) |
| `VECTOR_BACKEND` | `chroma` (dev) \| `pgvector` (prod) |
| `GITHUB_TOKEN` | outbound GitHub scan |

---

## 7. Build order (follows judging weight, not visual appeal)

1. **Memory + persistent Founder Score** (Epic B) — the 30% foundation.
2. **Thesis Engine + Screening + 3-axis scoring incl. cold-start** (Epics A, E) — 25–30%.
3. **Trust Score / evidence / contradiction** (Epic F).
4. **Memo generation + adversarial view** (Epic G) — decision utility, 30%.
5. **Dashboard** (Epic H) — 15%.
6. **Outbound sourcing + activation** (Epic D).
7. Stretch: agentic traceability (I1), validator agent (I2).

Rehearse the [demo script](VC_Brain_Requirements.md#10-end-to-end-demo-script-what-judges-should-see) before adding extras.

---

## 8. Scaling path (how this grows into PROJECT_PLAN.md)

| Hackathon (now) | Enterprise (later) — no rewrite, just swaps |
|---|---|
| SQLite | Postgres + TimescaleDB (score history) |
| Chroma | pgvector / Pinecone / Weaviate |
| APScheduler in-process | Redis + BullMQ / Celery (swap behind `app/workers`) |
| Modular monolith | Extract `memory`/`intelligence` modules into services (seams already clean) |
| Single-tenant | RBAC + multi-tenant (hooks already in `app/core/security`) |
