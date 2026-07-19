"""Agentic Traceability (Stretch I1) — the full reasoning chain, artifact-cited.

Assembles a step-by-step trace of how an opportunity moved from first signal to
decision, and resolves every conclusion back to the EXACT source artifacts (the
signals — deck slide, GitHub repo, web result) that drove it. This is what lets an
investor click a conclusion and see precisely what justified it.

It reads only already-persisted, structured outputs (thesis fit, screening, the
three axis scores + their cited evidence, memo claims + contradictions) — the
"chain-of-thought logging" is a property of the pipeline storing its work as it
goes, not a separate narration layer that could drift from what actually happened.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.intelligence.thesis_engine import score_thesis_fit
from app.memory.repository import MemoryRepository
from app.models.signal import Signal


def _artifact(sig: Signal | None) -> dict | None:
    if sig is None:
        return None
    return {
        "signal_id": sig.id,
        "source": sig.source,
        "record_type": sig.record_type,
        "confidence": sig.confidence,
        "excerpt": (sig.payload or {}).get("text") or sig.record_type,
        "external_url": sig.external_url,
        "timestamp": sig.source_timestamp.isoformat() if sig.source_timestamp else None,
    }


class TraceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MemoryRepository(db)

    def build(self, application_id: int) -> dict:
        app = self.repo.get_application(application_id)
        if app is None:
            raise ValueError(f"Application {application_id} not found")
        founder = self.repo.get_founder(app.founder_id)
        company = self.repo.get_company(app.company_id)
        signals = self.repo.signals_for(founder.id)
        pool = len(signals)

        steps: list[dict] = []

        # 1. Sourcing — how the founder entered the funnel.
        steps.append(
            {
                "stage": "Sourcing",
                "title": "Entered funnel",
                "conclusion": f"{app.channel.capitalize()} · {pool} signals in Memory",
                "rationale": (
                    "Discovered via outbound scan, then activated into the same funnel."
                    if app.channel == "outbound"
                    else "Founder applied directly (deck + company name)."
                ),
                "evidence": [_artifact(s) for s in signals[:4]],
                "pool": pool,
            }
        )

        # 2. Thesis fit.
        fit = score_thesis_fit(company, self.db)
        steps.append(
            {
                "stage": "Screening",
                "title": "Thesis fit",
                "conclusion": f"{fit.score}/100",
                "rationale": "; ".join(fit.reasons),
                "evidence": [],
                "pool": pool,
            }
        )

        # 3. First-pass screening (persisted decision).
        if app.screening_decision:
            steps.append(
                {
                    "stage": "Screening",
                    "title": "First-pass filter",
                    "conclusion": app.screening_decision.upper(),
                    "rationale": app.screening_reason or "",
                    "evidence": [],
                    "pool": pool,
                }
            )

        # 4-6. The three independent axes, each with its cited source artifacts.
        axis_titles = {"founder": "Founder axis", "market": "Market axis", "idea": "Idea-vs-Market axis"}
        for axis, row in self.repo.latest_axis_scores(application_id).items():
            cited = [_artifact(self.repo.signal_by_id(sid)) for sid in (row.evidence_ids or [])]
            cited = [c for c in cited if c]
            steps.append(
                {
                    "stage": "Screening",
                    "title": axis_titles.get(axis, axis),
                    "conclusion": f"{int(row.value)}/100 · {row.trend}",
                    "rationale": row.rationale or "",
                    "evidence": cited,
                    "pool": pool,
                    "axis": axis,
                }
            )

        # 7. Diligence — contradictions + evidence-backed memo + recommendation.
        memo = self.repo.latest_memo_for(application_id)
        if memo:
            contradicted = []
            claim_count = evidence_count = 0
            for section in memo.sections:
                for claim in section.claims:
                    claim_count += 1
                    ev = self._evidence_for(claim.id)
                    evidence_count += len(ev)
                    if claim.contradicted:
                        contradicted.append(
                            {
                                "claim": claim.text,
                                "evidence": [_artifact(self.repo.signal_by_id(e)) for e in ev],
                            }
                        )
            if contradicted:
                steps.append(
                    {
                        "stage": "Diligence",
                        "title": "Contradiction flagged",
                        "conclusion": f"{len(contradicted)} conflict(s) surfaced",
                        "rationale": "Claims that conflict with an independent source, flagged not resolved.",
                        "evidence": [a for c in contradicted for a in c["evidence"] if a],
                        "pool": pool,
                    }
                )

            steps.append(
                {
                    "stage": "Decision",
                    "title": "Recommendation",
                    "conclusion": f"{(memo.recommendation or 'n/a').upper()} · Trust {memo.trust_score}/100",
                    "rationale": (
                        f"Synthesised from {claim_count} claims across the memo, "
                        f"{evidence_count} of them evidence-linked. Trust Score reflects evidence "
                        f"quality, contradictions, and disclosed gaps."
                    ),
                    "evidence": [],
                    "pool": pool,
                    "memo_id": memo.id,
                }
            )

        return {
            "application_id": application_id,
            "founder_id": founder.id,
            "founder_name": founder.name,
            "company_name": company.name,
            "channel": app.channel,
            "is_cold_start": founder.is_cold_start,
            "signal_pool": pool,
            "steps": steps,
        }

    def _evidence_for(self, claim_id: int) -> list[int]:
        from sqlalchemy import select

        from app.models.evidence import Evidence

        return list(
            self.db.scalars(select(Evidence.signal_id).where(Evidence.claim_id == claim_id))
        )
