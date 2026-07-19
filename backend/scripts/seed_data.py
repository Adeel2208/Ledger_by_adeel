"""Seed the demo dataset (Requirements section 7).

The seed set deliberately includes, so the demo can show each capability:
  1. A founder with a strong public track record (GitHub, papers).
  2. A COLD-START founder — no funding, no GitHub, no network (E3 / cold-start).
  3. A founder with a SEEDED CONTRADICTION (claimed traction vs independent source)
     so the Trust Score / contradiction flag has something to catch (F2, I2).
  4. An INCOMPLETE profile with a genuinely missing field (cap table) so honest
     gap-flagging is demonstrable instead of fabrication (F3).

Runs fully OFFLINE (no API key / network): signals are synthetic and indexing is
disabled, so `python scripts/init_db.py && python scripts/seed_data.py` works out
of the box. The persistent Founder Score is computed deterministically from these.

Run:  python scripts/seed_data.py
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.memory.ingestion.base import IngestBundle, RawSignal
from app.models.score import AxisScore, FounderScore
from app.models.thesis import Thesis
from app.schemas.common import Confidence
from app.services.ingestion_service import IngestionService

NOW = datetime.now(timezone.utc)


def _seed_history(db, founder_id: int, application_id: int | None, latest_value: float) -> None:
    """Backdate one earlier score point per axis + founder score (E2 demo trend).

    The requirement allows simulated history for the demo: trend needs >=2 points.
    The backdated point is lower, so the next real scoring shows 'improving' arrows
    computed genuinely from the two points — nothing is faked at read time.
    """
    month_ago = NOW - timedelta(days=30)
    db.add(FounderScore(founder_id=founder_id, value=max(0, latest_value - 7),
                        momentum="stable", components={}, computed_at=month_ago))
    # Reflect the real trajectory on the latest stored point.
    latest = (db.query(FounderScore).filter(FounderScore.founder_id == founder_id)
              .order_by(FounderScore.computed_at.desc()).first())
    if latest:
        latest.momentum = "improving"
    if application_id:
        for axis, v in (("founder", 64.0), ("market", 70.0), ("idea", 62.0)):
            db.add(AxisScore(application_id=application_id, axis=axis, value=v,
                             trend="stable", rationale="(baseline, one month ago)",
                             evidence_ids=[], scored_at=month_ago))
    db.commit()


def _sig(source, rtype, text, conf, days_ago=0, **payload) -> RawSignal:
    return RawSignal(
        source=source,
        record_type=rtype,
        payload={"text": text, **payload},
        timestamp=NOW - timedelta(days=days_ago),
        confidence=conf,
        external_url=payload.get("url"),
        text=text,
    )


def _default_thesis(db) -> None:
    if db.query(Thesis).first():
        return
    db.add(
        Thesis(
            name="default",
            sectors=["AI", "DevTools", "FinTech"],
            stages=["pre-seed", "seed"],
            geographies=["Europe", "US"],
            check_size_min=50_000,
            check_size_max=250_000,
            ownership_target=0.10,
            risk_appetite="moderate",
        )
    )
    db.commit()


def seed() -> None:
    db = SessionLocal()
    svc = IngestionService(db)
    try:
        _default_thesis(db)

        # 1. Strong track-record founder (outbound-discoverable via GitHub + papers).
        ada = svc.ingest_bundle(
            IngestBundle(
                identity={"name": "Ada Vance", "github_handle": "adavance", "email": "ada@vance.dev"},
                company={"name": "InferGrid", "sector": "AI", "stage": "seed", "geography": "Berlin"},
                signals=[
                    _sig("github", "github_profile",
                         "GitHub adavance: 3.1k followers, 14 original repos, 22k stars.",
                         Confidence.VERIFIED, 5, url="https://github.com/adavance"),
                    _sig("github", "github_repo",
                         "Repo tensor-sched (Rust), 9.4k stars: distributed GPU scheduler.",
                         Confidence.VERIFIED, 12),
                    _sig("arxiv", "research_paper",
                         "Paper: Elastic Scheduling for LLM Training. Cited 140x.",
                         Confidence.VERIFIED, 200),
                    _sig("deck", "traction_claim",
                         "Design partners: 3 GPU clouds signed LOIs.",
                         Confidence.CLAIMED, 3),
                ],
            ),
            channel="outbound",   # Ada was discovered via GitHub, not an inbound application
            index=False,
        )
        # E2: backdated score history so trend arrows are visible in the demo.
        _seed_history(db, ada.founder_id, ada.application_id,
                      latest_value=(ada.founder_score or {}).get("value", 50.0))

        # 2. Cold-start founder — NO github/funding/network; alternate signals only.
        svc.ingest_bundle(
            IngestBundle(
                identity={"name": "Rosa Individ"},  # no email/handle on purpose
                company={"name": "ClinicLoop", "sector": "HealthTech", "stage": "pre-seed", "geography": "Lisbon"},
                signals=[
                    _sig("web", "public_footprint",
                         "Detailed blog series on triage workflow failures from 6 yrs as an ER nurse.",
                         Confidence.SCRAPED, 20, url="https://rosa.blog/triage"),
                    _sig("web", "public_footprint",
                         "Shipped a working Streamlit triage-prioritisation demo, 400 upvotes on a nursing forum.",
                         Confidence.SCRAPED, 15),
                    _sig("deck", "problem_statement",
                         "Problem framed from lived ER experience: mis-triage under load.",
                         Confidence.CLAIMED, 2),
                ],
            ),
            is_cold_start=True,
            index=False,
        )

        # 3. Contradiction founder — claimed MRR conflicts with an independent source.
        svc.ingest_bundle(
            IngestBundle(
                identity={"name": "Max Bloom", "github_handle": "maxbloom"},
                company={"name": "PayPlex", "sector": "FinTech", "stage": "seed", "geography": "London"},
                signals=[
                    # Seeded contradiction (F2): numerically impossible vs the independent source.
                    _sig("deck", "traction_claim",
                         "Deck claims 40,000 paying customers and $2.4M ARR as of Q2.",
                         Confidence.CLAIMED, 4, value="40000_customers"),
                    _sig("producthunt", "product_launch",
                         "Independent: Show HN launch 3 months ago got 60 points; founder's own comments cite exactly 15 paying teams total.",
                         Confidence.CORROBORATED, 30, value="15_customers"),
                    _sig("github", "github_profile",
                         "GitHub maxbloom: 40 followers, 3 original repos.",
                         Confidence.VERIFIED, 6),
                ],
            ),
            index=False,
        )

        # 4. Incomplete profile — genuinely missing data (no cap table / financials).
        svc.ingest_bundle(
            IngestBundle(
                identity={"name": "Jun Park", "email": "jun@nimbus.io"},
                company={"name": "Nimbus", "sector": "DevTools", "stage": "pre-seed", "geography": "Seoul"},
                signals=[
                    _sig("deck", "problem_statement",
                         "CI caching is slow for monorepos; Nimbus proposes content-addressed cache.",
                         Confidence.CLAIMED, 1),
                    # No traction, team_background, or market_size signals -> gaps get flagged honestly.
                ],
            ),
            index=False,
        )

        # 5. DISCOVERED founder — outbound-scanned, no application yet (D1/D3 demo):
        #    appears on the Sourcing watchlist with an "Activate" action.
        svc.ingest_bundle(
            IngestBundle(
                identity={"name": "Leo Torres", "github_handle": "leotorres-dev"},
                company={},  # no company yet -> no application -> watchlist
                signals=[
                    _sig("github", "github_profile",
                         "GitHub leotorres-dev: 800 followers, 9 original repos, 4.2k stars; building an open-source eval harness for agents.",
                         Confidence.VERIFIED, 2, url="https://github.com/leotorres-dev"),
                    _sig("github", "github_repo",
                         "Repo agent-evals (Python), 3.1k stars: reproducible eval harness for LLM agents.",
                         Confidence.VERIFIED, 6),
                ],
            ),
            channel="outbound",
            index=False,
        )

        print("Seeded 4 opportunities + 1 discovered founder (watchlist) + default thesis.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
