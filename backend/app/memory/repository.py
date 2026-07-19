"""Data access for the Memory layer (repository pattern).

All reads/writes for founders, companies, signals, and founder-score history go
through here, so higher layers never touch the ORM session directly.
"""
from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.memory.ingestion.base import RawSignal
from app.models.application import Application
from app.models.company import Company
from app.models.evidence import Evidence
from app.models.founder import Founder
from app.models.memo import Claim, Memo, MemoSection
from app.models.score import AxisScore, FounderScore
from app.models.signal import Signal


class MemoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Founders ──────────────────────────────────────────────────────────────
    def create_founder(self, identity: dict, *, is_cold_start: bool = False) -> Founder:
        founder = Founder(
            name=identity.get("name") or "Unknown",
            email=identity.get("email"),
            github_handle=identity.get("github_handle"),
            linkedin_url=identity.get("linkedin_url"),
            is_cold_start=is_cold_start,
        )
        self.db.add(founder)
        self.db.flush()
        return founder

    def get_founder(self, founder_id: int) -> Founder | None:
        return self.db.get(Founder, founder_id)

    def list_founders(self) -> list[Founder]:
        return list(self.db.scalars(select(Founder).order_by(Founder.created_at.desc())))

    def enrich_founder_identity(self, founder: Founder, identity: dict) -> None:
        """Fill only missing identity fields (never overwrite verified data)."""
        for attr in ("email", "github_handle", "linkedin_url"):
            if not getattr(founder, attr) and identity.get(attr):
                setattr(founder, attr, identity[attr])
        if (founder.name in (None, "Unknown")) and identity.get("name"):
            founder.name = identity["name"]
        self.db.flush()

    # ── Companies ─────────────────────────────────────────────────────────────
    def create_company(self, data: dict) -> Company:
        company = Company(
            name=data.get("name") or "Unknown",
            sector=data.get("sector"),
            stage=data.get("stage"),
            geography=data.get("geography"),
        )
        self.db.add(company)
        self.db.flush()
        return company

    # ── Signals ───────────────────────────────────────────────────────────────
    def add_signal(self, founder_id: int | None, raw: RawSignal) -> Signal:
        signal = Signal(
            founder_id=founder_id,
            source=raw.source,
            record_type=raw.record_type,
            confidence=raw.confidence.value if hasattr(raw.confidence, "value") else raw.confidence,
            payload=raw.payload,
            external_url=raw.external_url,
            source_timestamp=raw.timestamp,
        )
        self.db.add(signal)
        self.db.flush()
        return signal

    def signals_for(self, founder_id: int) -> list[Signal]:
        return list(
            self.db.scalars(
                select(Signal).where(Signal.founder_id == founder_id).order_by(desc(Signal.source_timestamp))
            )
        )

    # ── Persistent Founder Score ──────────────────────────────────────────────
    def add_founder_score(
        self, founder_id: int, value: float, momentum: str | None, components: dict
    ) -> FounderScore:
        row = FounderScore(
            founder_id=founder_id, value=value, momentum=momentum, components=components
        )
        self.db.add(row)
        self.db.flush()
        return row

    def score_history(self, founder_id: int) -> list[FounderScore]:
        return list(
            self.db.scalars(
                select(FounderScore)
                .where(FounderScore.founder_id == founder_id)
                .order_by(FounderScore.computed_at)
            )
        )

    def latest_score(self, founder_id: int) -> FounderScore | None:
        return self.db.scalars(
            select(FounderScore)
            .where(FounderScore.founder_id == founder_id)
            .order_by(desc(FounderScore.computed_at))
            .limit(1)
        ).first()

    # ── Opportunities (Company + Application) ─────────────────────────────────
    def create_application(
        self, founder_id: int, company_id: int, channel: str
    ) -> Application:
        app = Application(founder_id=founder_id, company_id=company_id, channel=channel)
        self.db.add(app)
        self.db.flush()
        return app

    def get_application(self, application_id: int) -> Application | None:
        return self.db.get(Application, application_id)

    def list_applications(self) -> list[Application]:
        return list(self.db.scalars(select(Application).order_by(desc(Application.created_at))))

    def get_company(self, company_id: int) -> Company | None:
        return self.db.get(Company, company_id)

    def set_screening(self, application_id: int, decision: str, reason: str) -> None:
        app = self.get_application(application_id)
        app.screening_decision = decision
        app.screening_reason = reason
        self.db.flush()

    # ── Axis scores (the three independent axes over time) ────────────────────
    def add_axis_score(
        self,
        application_id: int,
        axis: str,
        value: float,
        trend: str | None,
        rationale: str | None,
        evidence_ids: list[int],
    ) -> AxisScore:
        row = AxisScore(
            application_id=application_id,
            axis=axis,
            value=value,
            trend=trend,
            rationale=rationale,
            evidence_ids=evidence_ids,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def axis_history(self, application_id: int, axis: str) -> list[AxisScore]:
        return list(
            self.db.scalars(
                select(AxisScore)
                .where(AxisScore.application_id == application_id, AxisScore.axis == axis)
                .order_by(AxisScore.scored_at)
            )
        )

    def latest_axis_scores(self, application_id: int) -> dict[str, AxisScore]:
        """Most recent score per axis, keyed by axis name."""
        rows = self.db.scalars(
            select(AxisScore)
            .where(AxisScore.application_id == application_id)
            .order_by(AxisScore.scored_at)
        )
        latest: dict[str, AxisScore] = {}
        for row in rows:
            latest[row.axis] = row  # later rows overwrite -> ends on newest
        return latest

    # ── Memo (memo -> sections -> claims -> evidence) ─────────────────────────
    def create_memo(self, application_id: int) -> Memo:
        memo = Memo(application_id=application_id)
        self.db.add(memo)
        self.db.flush()
        return memo

    def add_section(self, memo_id: int, title: str, body: str, is_gap: bool = False) -> MemoSection:
        section = MemoSection(memo_id=memo_id, title=title, body=body, is_gap=is_gap)
        self.db.add(section)
        self.db.flush()
        return section

    def add_claim(
        self, section_id: int, text: str, confidence: str, contradicted: bool = False
    ) -> Claim:
        claim = Claim(
            section_id=section_id, text=text, confidence=confidence, contradicted=contradicted
        )
        self.db.add(claim)
        self.db.flush()
        return claim

    def add_evidence(
        self, claim_id: int, signal_id: int, confidence: str, note: str | None = None
    ) -> Evidence:
        ev = Evidence(claim_id=claim_id, signal_id=signal_id, confidence=confidence, note=note)
        self.db.add(ev)
        self.db.flush()
        return ev

    def finalize_memo(self, memo_id: int, recommendation: str, trust_score: float) -> None:
        memo = self.db.get(Memo, memo_id)
        memo.recommendation = recommendation
        memo.trust_score = trust_score
        self.db.flush()

    def get_memo(self, memo_id: int) -> Memo | None:
        return self.db.get(Memo, memo_id)

    def latest_memo_for(self, application_id: int) -> Memo | None:
        return self.db.scalars(
            select(Memo)
            .where(Memo.application_id == application_id)
            .order_by(desc(Memo.created_at))
            .limit(1)
        ).first()

    def signal_by_id(self, signal_id: int) -> Signal | None:
        return self.db.get(Signal, signal_id)
