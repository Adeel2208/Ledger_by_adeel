"""Ingestion orchestrator — the ECL pipeline (Extract -> Cognify -> Load).

Ties the Memory layer together for one source pull:

    connector.fetch()          # EXTRACT + COGNIFY (raw source -> identity + signals)
      -> dedup.resolve()       # entity resolution (attach to the right founder)
      -> repository persist     # LOAD relational golden record + provenance
      -> vector index upsert    # LOAD semantic index over the signals
      -> recompute FounderScore # persistent, cross-application

Lives in the service layer because it spans Memory (repository, dedup, score) and
the vector index (intelligence/retrieval), keeping the Memory modules themselves
free of any upward dependency (principle #2).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.intelligence.retrieval import get_index
from app.memory import dedup
from app.memory.founder_score import compute_founder_score
from app.memory.ingestion.base import IngestBundle
from app.memory.ingestion.registry import get_connector
from app.memory.repository import MemoryRepository
from app.models.founder import Founder

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    founder_id: int
    founder_name: str
    dedup_action: str
    dedup_reasons: list[str]
    signals_added: int
    needs_review: bool
    founder_score: dict | None = None
    application_id: int | None = None      # the opportunity created for this ingest, if any
    warnings: list[str] = field(default_factory=list)


class IngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MemoryRepository(db)

    def ingest(
        self,
        source: str,
        *,
        is_cold_start: bool = False,
        index: bool = True,
        channel: str = "outbound",
        **params,
    ) -> IngestResult:
        connector = get_connector(source)
        bundle = connector.fetch(**params)
        return self._load(bundle, is_cold_start=is_cold_start, index=index, channel=channel)

    def ingest_bundle(
        self,
        bundle: IngestBundle,
        *,
        is_cold_start: bool = False,
        index: bool = True,
        channel: str = "inbound",
    ) -> IngestResult:
        """Load an already-fetched bundle (used by seeding / synthetic data)."""
        return self._load(bundle, is_cold_start=is_cold_start, index=index, channel=channel)

    # ── internal ──────────────────────────────────────────────────────────────
    def _load(
        self, bundle: IngestBundle, *, is_cold_start: bool, index: bool = True, channel: str = "inbound"
    ) -> IngestResult:
        warnings: list[str] = []

        # 1. Entity resolution — attach to an existing founder or create a new one.
        decision = dedup.resolve(bundle.identity, self.db)
        if decision.action is dedup.Action.MERGE and decision.founder_id:
            founder = self.repo.get_founder(decision.founder_id)
            self.repo.enrich_founder_identity(founder, bundle.identity)
        elif decision.action is dedup.Action.REVIEW and decision.founder_id:
            # Ambiguous: attach to the best candidate but flag for a human (never silently split/merge).
            founder = self.repo.get_founder(decision.founder_id)
            warnings.append(
                f"Ambiguous identity match (score {decision.score:.2f}) — flagged for review."
            )
        else:
            founder = self.repo.create_founder(bundle.identity, is_cold_start=is_cold_start)

        # 2. Persist signals (relational golden record + provenance).
        stored = [self.repo.add_signal(founder.id, raw) for raw in bundle.signals]

        # 3. Index signal text for semantic retrieval (skip signals with no text).
        if index:
            self._index(founder, bundle, stored)

        # 4. Recompute the persistent Founder Score from all-time signals.
        score = None
        if stored:
            score = compute_founder_score(founder.id, self.db)

        # 5. Create the opportunity (Company + Application) when company info is present,
        #    so downstream screening/scoring has a unit to evaluate. Channel is recorded
        #    but never fed into any scorer (inbound == outbound on the merits).
        application_id = None
        if bundle.company.get("name"):
            company = self.repo.create_company(bundle.company)
            application_id = self.repo.create_application(founder.id, company.id, channel).id

        self.db.commit()
        return IngestResult(
            founder_id=founder.id,
            founder_name=founder.name,
            dedup_action=decision.action.value,
            dedup_reasons=decision.reasons,
            signals_added=len(stored),
            needs_review=decision.action is dedup.Action.REVIEW,
            founder_score=score,
            application_id=application_id,
            warnings=warnings,
        )

    def _index(self, founder: Founder, bundle: IngestBundle, stored: list) -> None:
        ids, texts, metas = [], [], []
        for raw, signal in zip(bundle.signals, stored):
            if not raw.text:
                continue
            ids.append(f"signal:{signal.id}")
            texts.append(raw.text)
            metas.append(
                {
                    "signal_id": signal.id,
                    "founder_id": founder.id,
                    "source": signal.source,
                    "record_type": signal.record_type,
                    "confidence": signal.confidence,
                }
            )
        if not ids:
            return
        try:
            get_index().upsert(ids, texts, metas)
        except Exception as exc:  # index is best-effort; relational truth already saved
            logger.warning("Vector index upsert failed: %s", exc)
