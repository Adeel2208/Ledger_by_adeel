"""Memo generation service (FR-8, FR-9, Epics F & G) — the decision-ready output.

Orchestrates the diligence step:
  1. Gather context — company, founder, signals (ID-tagged), the three axis scores,
     thesis fit, data-coverage gaps, and detected contradictions.
  2. Generate the memo as structured JSON (5 required sections + adversarial view +
     recommendation), each claim citing signal IDs.
  3. Persist Memo -> Sections -> Claims -> Evidence, reconciling each claim's stated
     confidence against its actual cited evidence (a claim can't outrank its sources).
  4. Flag contradictions on affected claims; disclose gaps as explicit gap sections.
  5. Compute the Trust Score from evidence quality, contradictions, and gaps.

`llm` is injectable so the whole flow runs offline with a fake provider in tests.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.intelligence.scoring.base import signal_context
from app.intelligence.trust.contradiction import detect_contradictions
from app.intelligence.trust.evidence_tracer import compute_trust_score, reconcile_claim_confidence
from app.memory.enrichment import assess
from app.memory.repository import MemoryRepository
from app.models.evidence import Evidence
from app.schemas.memo import MemoLLM, MemoSectionLLM

_SYSTEM = (
    "You are a VC analyst writing a decision-ready investment memo. Rules you MUST follow:\n"
    "- Ground every claim in the provided signals and cite their numeric IDs.\n"
    "- Never fabricate data. If something needed for the decision is missing, add it to "
    "disclosed_gaps (e.g. 'Cap table: not disclosed') and keep the related section brief.\n"
    "- Set each claim's confidence to reflect its cited evidence, not your optimism.\n"
    "- Be concise; padding counts against you. Include a genuine adversarial/bear view.\n"
    "- recommendation is exactly one of: invest | pass | need_more_info."
)


class MemoService:
    def __init__(self, db: Session, llm=None) -> None:
        self.db = db
        self.repo = MemoryRepository(db)
        self._llm = llm

    @property
    def llm(self):
        if self._llm is None:
            from app.llm.client import get_llm

            self._llm = get_llm()
        return self._llm

    def generate(self, application_id: int) -> int:
        app = self.repo.get_application(application_id)
        if app is None:
            raise ValueError(f"Application {application_id} not found")
        company = self.repo.get_company(app.company_id)
        founder = self.repo.get_founder(app.founder_id)
        signals = self.repo.signals_for(founder.id)
        scores = self.repo.latest_axis_scores(application_id)
        coverage = assess(founder.id, self.db)

        # Detect contradictions first so the memo prompt is aware of them.
        contradictions = detect_contradictions(application_id, self.db, self._llm)
        contradicted_signal_ids = {
            sid for c in contradictions for sid in (c.signal_id_a, c.signal_id_b)
        }

        memo_llm = self._draft(company, founder, signals, scores, coverage, contradictions)

        # Persist.
        memo = self.repo.create_memo(application_id)
        valid_ids = {s.id for s in signals}
        claim_confidences: list[str] = []

        required = {
            "Company Snapshot": memo_llm.company_snapshot,
            "Investment Hypotheses": memo_llm.investment_hypotheses,
            "SWOT": memo_llm.swot,
            "Problem & Product": memo_llm.problem_and_product,
            "Traction & KPIs": memo_llm.traction_and_kpis,
            "Adversarial / Risk View": memo_llm.adversarial_view,
        }
        for title, section in required.items():
            self._persist_section(
                memo.id, title, section, valid_ids, contradicted_signal_ids, claim_confidences
            )

        # Explicit gap sections — disclosed, never fabricated (F3).
        for gap in memo_llm.disclosed_gaps:
            self.repo.add_section(memo.id, "Data Gap", gap, is_gap=True)

        # Recommendation section.
        self.repo.add_section(
            memo.id,
            "Recommendation",
            f"{memo_llm.recommendation.upper()} — {memo_llm.recommendation_rationale}",
        )

        trust = compute_trust_score(claim_confidences, contradictions, len(memo_llm.disclosed_gaps))
        self.repo.finalize_memo(memo.id, memo_llm.recommendation, trust)
        self.db.commit()
        return memo.id

    # ── internal ──────────────────────────────────────────────────────────────
    def _persist_section(
        self, memo_id, title, section: MemoSectionLLM, valid_ids, contradicted_ids, confidences
    ) -> None:
        row = self.repo.add_section(memo_id, title, section.summary)
        for claim in section.claims:
            cited = [sid for sid in claim.evidence_signal_ids if sid in valid_ids]
            tiers = [self.repo.signal_by_id(sid).confidence for sid in cited]
            confidence = reconcile_claim_confidence(claim.confidence, tiers)
            contradicted = any(sid in contradicted_ids for sid in cited)
            claim_row = self.repo.add_claim(row.id, claim.text, confidence.value, contradicted)
            for sid in cited:
                self.repo.add_evidence(claim_row.id, sid, self.repo.signal_by_id(sid).confidence)
            confidences.append(confidence.value)

    def _draft(self, company, founder, signals, scores, coverage, contradictions) -> MemoLLM:
        score_lines = "\n".join(
            f"- {axis}: {row.value}/100 ({row.trend}) — {row.rationale}"
            for axis, row in scores.items()
        ) or "- (not yet scored)"
        contra_lines = "\n".join(
            f"- signals {c.signal_id_a} vs {c.signal_id_b} [{c.severity}]: {c.description}"
            for c in contradictions
        ) or "- none detected"
        prompt = (
            f"COMPANY: {company.name} | sector={company.sector} | stage={company.stage} "
            f"| geography={company.geography}\n"
            f"FOUNDER: {founder.name}"
            f"{' (COLD-START: judged on alternate signals)' if founder.is_cold_start else ''}\n\n"
            f"THREE INDEPENDENT AXIS SCORES (do NOT average these):\n{score_lines}\n\n"
            f"KNOWN CONTRADICTIONS (flag these, do not resolve silently):\n{contra_lines}\n\n"
            f"DATA GAPS detected (facets with no signal): {coverage['gaps']}\n\n"
            f"EVIDENCE SIGNALS (cite by ID):\n{signal_context(signals)}\n\n"
            "Write the memo now."
        )
        return self.llm.structured(prompt, MemoLLM, system=_SYSTEM)

    # ── read side ─────────────────────────────────────────────────────────────
    def get_full(self, memo_id: int) -> dict:
        memo = self.repo.get_memo(memo_id)
        if memo is None:
            raise ValueError(f"Memo {memo_id} not found")
        sections = []
        for section in memo.sections:
            claims = []
            for claim in section.claims:
                claims.append(
                    {
                        "text": claim.text,
                        "confidence": claim.confidence,
                        "contradicted": claim.contradicted,
                        "evidence": [self._evidence_view(ev) for ev in self._evidence_for(claim.id)],
                    }
                )
            sections.append(
                {
                    "title": section.title,
                    "body": section.body,
                    "is_gap": section.is_gap,
                    "claims": claims,
                }
            )
        return {
            "id": memo.id,
            "application_id": memo.application_id,
            "recommendation": memo.recommendation,
            "trust_score": memo.trust_score,
            "sections": sections,
        }

    def _evidence_for(self, claim_id: int) -> list[Evidence]:
        return list(self.db.scalars(select(Evidence).where(Evidence.claim_id == claim_id)))

    def _evidence_view(self, ev: Evidence) -> dict:
        signal = self.repo.signal_by_id(ev.signal_id)
        return {
            "signal_id": ev.signal_id,
            "confidence": ev.confidence,
            "source": signal.source if signal else None,
            "external_url": signal.external_url if signal else None,
        }
