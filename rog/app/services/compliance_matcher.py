from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from rog.app.models.compliance_status import ComplianceStatus
from rog.app.models.obligation import Obligation
from rog.app.services.document_processor import extract_text_from_docx, extract_text_from_pdf

logger = logging.getLogger(__name__)

STATUS_COMPLIANT = "COMPLIANT"
STATUS_NON_COMPLIANT = "NON_COMPLIANT"
STATUS_UNKNOWN = "UNKNOWN"

RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"
RISK_CRITICAL = "CRITICAL"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{3,}", text.lower())}


def _compute_risk(obligation: Obligation) -> str:
    score = 0
    if obligation.penalty_text:
        score += 2
    if obligation.deadline_text:
        score += 1
    if obligation.mandatory_flag:
        score += 1

    if score >= 4:
        return RISK_CRITICAL
    if score == 3:
        return RISK_HIGH
    if score == 2:
        return RISK_MEDIUM
    return RISK_LOW


class ComplianceMatcher:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _extract_document_text(self, *, file_path: str, file_type: str) -> str:
        if file_type == "pdf":
            return extract_text_from_pdf(file_path)
        if file_type == "docx":
            return extract_text_from_docx(file_path)
        raise ValueError(f"Unsupported company document file_type: {file_type}")

    def _determine_status(self, obligation: Obligation, doc_text: str) -> str:
        obligation_text = _normalize(obligation.action_text or "")
        if not obligation_text:
            return STATUS_UNKNOWN
        obligation_tokens = _tokenize(obligation_text)
        if not obligation_tokens:
            return STATUS_UNKNOWN

        doc_tokens = _tokenize(doc_text)
        overlap_ratio = len(obligation_tokens & doc_tokens) / max(len(obligation_tokens), 1)
        if overlap_ratio >= 0.5:
            return STATUS_COMPLIANT
        if overlap_ratio <= 0.15:
            return STATUS_NON_COMPLIANT
        return STATUS_UNKNOWN

    def match_company_document(
        self,
        *,
        company_id: uuid.UUID,
        file_path: str,
        file_type: str,
    ) -> int:
        logger.info("compliance_matching_start company_id=%s file_type=%s", company_id, file_type)
        try:
            doc_text = _normalize(self._extract_document_text(file_path=file_path, file_type=file_type))
            obligations = self.db.scalars(select(Obligation)).all()
            updated = 0
            for obligation in obligations:
                status = self._determine_status(obligation, doc_text)
                risk_level = _compute_risk(obligation)

                existing = self.db.scalar(
                    select(ComplianceStatus).where(
                        ComplianceStatus.company_id == company_id,
                        ComplianceStatus.obligation_id == obligation.id,
                    )
                )
                if existing is None:
                    self.db.add(
                        ComplianceStatus(
                            company_id=company_id,
                            obligation_id=obligation.id,
                            status=status,
                            risk_level=risk_level,
                            last_checked=datetime.now(timezone.utc),
                        )
                    )
                else:
                    existing.status = status
                    existing.risk_level = risk_level
                    existing.last_checked = datetime.now(timezone.utc)
                    self.db.add(existing)
                updated += 1

            logger.info("compliance_matching_results company_id=%s obligations_checked=%s", company_id, updated)
            return updated
        except Exception:
            logger.exception("compliance_matching_failure company_id=%s", company_id)
            raise

    def get_company_compliance(self, company_id: uuid.UUID) -> list[ComplianceStatus]:
        return self.db.scalars(
            select(ComplianceStatus)
            .where(ComplianceStatus.company_id == company_id)
            .order_by(ComplianceStatus.last_checked.desc())
        ).all()

    def get_high_risk_obligations(self, company_id: uuid.UUID) -> list[ComplianceStatus]:
        return self.db.scalars(
            select(ComplianceStatus).where(
                ComplianceStatus.company_id == company_id,
                ComplianceStatus.risk_level.in_([RISK_HIGH, RISK_CRITICAL]),
            )
        ).all()

    def get_non_compliant_obligations(self, company_id: uuid.UUID) -> list[ComplianceStatus]:
        return self.db.scalars(
            select(ComplianceStatus).where(
                ComplianceStatus.company_id == company_id,
                ComplianceStatus.status == STATUS_NON_COMPLIANT,
            )
        ).all()

