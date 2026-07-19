# The VC Brain

> An AI deal-flow operating system that finds exceptional founders **before** they fundraise and gets a $100K investment recommendation to decision-ready status in **24 hours** — not because of who they know, but because of what the system already knows about them.

Built for **Challenge #02 — Maschmeyer Group × Hack-Nation** (6th Global AI Hackathon, with MIT Club of Northern California & MIT Club of Germany).

---

## The idea in one screen

Four-stage pipeline — **Sourcing → Screening → Diligence → Decision** — over three architectural layers:

| Layer | Does | Code |
|---|---|---|
| **Memory** | Ingests decks, GitHub, launches, papers, web; dedups, enriches, timestamps & source-tags everything; holds the **persistent Founder Score** | [`backend/app/memory`](backend/app/memory) |
| **Intelligence** | Thesis Engine, fast screening, **three independent axis scores**, cold-start scoring, Trust Score, contradiction detection | [`backend/app/intelligence`](backend/app/intelligence) |
| **Experience** | Investor dashboard, decision-ready memo, agentic reasoning trace | [`frontend`](frontend) + [`backend/app/api`](backend/app/api) |

Full design: [ARCHITECTURE.md](ARCHITECTURE.md) · scoring & cold-start methods: [docs/](docs) · design system: [design-system/the-vc-brain/MASTER.md](design-system/the-vc-brain/MASTER.md).

---

## What it does (mapped to the brief)

- **Thesis Engine** — investor sets sectors / stage / geography / check size / ownership / risk; every opportunity is filtered & scored through that lens, applied *identically* to inbound and outbound. *(configurable, never hardcoded)*
- **Smart data collection** — 6 source connectors (GitHub, arXiv, Product Hunt/HN, deck parser for PDF/PPTX/DOCX, generic web, **Tavily**). Every signal stored with `source · timestamp · confidence · type`. Production **entity resolution** (blocking → Jaro-Winkler → confidence-banded merge/review/new).
- **Persistent Founder Score** — a "credit score for founders" that lives in Memory, follows the person across ventures, and **never resets**; surfaces momentum, not just a snapshot. Cold-start founders are scored by an **explicit alternate method** (public footprint, technical artifacts) — never defaulted to a low score.
- **Inbound** — apply with **deck + company name only** → deck parsed to slide-tagged claims → fast first-pass screening (pass / fail / **review**, always with a reason).
- **Outbound** — scan GitHub/etc. → discovered founders on a watchlist → **Activate** → converge into the *same* screening funnel as inbound.
- **Multi-axis screening** — **Founder / Market / Idea-vs-Market**, three **independent, never-averaged** scores, each with a trend (↑ / → / ↓).
- **Evidence-backed memo + Trust Score** — 5 required sections + adversarial view; **every claim traces to a source with a confidence tier**; contradictions flagged (not resolved); missing data disclosed (never fabricated). Trust Score is **per-claim**, not one company number.
- **Agentic Traceability** (stretch) — a full **reasoning trace**: every step from first signal to decision, each conclusion resolved to the **exact source artifact** that drove it.
- **Validator agent** (stretch) — cross-checks founder claims against external web data via Tavily.

### Non-negotiables (enforced in code + tests)
Three axes never averaged · missing data flagged never fabricated · Founder Score never resets · same scoring for inbound & outbound · no portfolio/follow-on/fund-ops/exit features.

---

## Stack

- **Backend** — Python 3.11 · FastAPI · SQLAlchemy 2.0 · SQLite (dev) / Postgres+pgvector (prod) · Chroma vectors
- **AI** — OpenAI (config-driven; defaults to `gpt-5.6-terra` reasoning / `gpt-5.6-luna` extraction · `text-embedding-3-large`), all **structured JSON** outputs
- **Frontend** — React · Vite · TypeScript · Tailwind · TanStack Query · Recharts · Lucide

---

## Run it

**Prerequisites:** Python 3.11+, Node 18+, an OpenAI API key.

### 1. Backend
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate          # Windows Git Bash  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt

cp .env.example .env                    # then edit .env: set OPENAI_API_KEY (TAVILY_API_KEY optional)

python scripts/init_db.py               # create tables
python scripts/seed_data.py             # load demo dataset (offline, no API calls)

uvicorn app.main:app --reload           # → http://localhost:8000/docs
```

### 2. Frontend
```bash
cd frontend
cp .env.example .env                    # VITE_API_BASE_URL defaults to localhost:8000
npm install
npm run dev                             # → http://localhost:5173
```

> Tests: `cd backend && PYTHONPATH=. pytest` (18 guardrail tests, run fully offline).

---

## Demo dataset

`scripts/seed_data.py` seeds the exact archetypes the brief asks for, **offline**:
- a **strong track-record** founder (GitHub + papers, outbound-discovered, with score history → trend arrows),
- a **cold-start** founder (no GitHub/funding/network → alternate scoring),
- a **seeded contradiction** (deck claims 40,000 customers / $2.4M ARR vs. an independent source citing 15 paying teams → flagged),
- an **incomplete** profile (missing data → disclosed as gaps),
- a **discovered** founder on the outbound watchlist (awaiting activation).

---

## The 24-hour journey (demo script)

1. **Thesis** (`/thesis`) — set the fund's lens; the deal flow re-ranks.
2. **Inbound** (`/apply`) — a founder submits deck + company name → screened in seconds.
3. **Outbound** (`/sourcing`) — scan a GitHub user → watchlist → **Activate** → same funnel.
4. **Deal Flow** (`/dashboard`) — ranked opportunities, three axis scores + trend, cold-start & screening tags. Click **Score**.
5. **Memo** — generate → 5 sections, per-claim evidence + confidence, contradiction flags, disclosed gaps, Trust Score, recommendation.
6. **Reasoning trace** — from the memo, open the full **agentic trace**: every step linked to its exact source artifact.

---

## Repo map
```
backend/    FastAPI modular monolith (Memory / Intelligence / Experience)
frontend/   React investor dashboard
docs/       Architecture deep-dives (scoring, cold-start, data model)
design-system/  Persisted UI design system (ui-ux-pro-max)
infra/      Docker & deployment
```
