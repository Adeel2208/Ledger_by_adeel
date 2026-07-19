# Scoring Model

## The three axes (never averaged)

Every opportunity gets **three independent scores** (FR-6). This is a hard non-negotiable:
there is no composite number anywhere in the system — not in the DB, not in the API, not in
the UI. `TripleScore` (`intelligence/scoring/base.py`) deliberately exposes no `.overall`.

| Axis | Question | Output |
|---|---|---|
| **Founder** | Who are they? Traits, track record, execution ability. | 0–100 + trend |
| **Market** | Sizing, competitors, SWOT. | bullish / neutral / bear + trend |
| **Idea vs. Market** | Does the idea survive scrutiny as-is, or is the team strong enough to pivot? | 0–100 + trend |

The Founder axis takes the **persistent Founder Score** as *one input*, not a replacement
(FR-7). The cold-start method feeds this axis when track-record signal is absent — see
[COLD_START.md](COLD_START.md).

## Trend (momentum, not snapshot)

Each axis carries a direction — improving / stable / declining — computed from ≥2 historical
score points (`scoring/trend.py`). For the demo, history can be seeded across two timestamps.

## Thesis fit (separate from the axes)

The Thesis Engine (FR-1) produces a 0–100 **thesis-fit** score used for *ranking/filtering*,
applied identically to inbound and outbound founders. It is orthogonal to the three axes and
never merged into them.

## Trust Score (data quality, not opportunity quality)

The Trust Score (FR-8) rates the *evidence*, not the deal. Each memo claim links to Evidence
rows with a confidence tier:

```
verified   > corroborated > claimed
(independent   (2+ sources    (founder-
 confirmation)  agree)         asserted only)
```

- Claims with no Evidence **cannot** be marked verified (enforced by the data model).
- Contradictions between sources are flagged, never silently resolved (`trust/contradiction.py`).
- Missing data is disclosed explicitly ("Cap table: not disclosed"), never fabricated.

## Consistency guarantee

The same scoring code path runs for inbound and outbound founders (NFR: Consistency). Sourcing
channel is recorded on the `Application` but is never an input to any scorer.
