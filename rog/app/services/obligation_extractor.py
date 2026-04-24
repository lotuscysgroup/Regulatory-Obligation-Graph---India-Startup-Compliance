from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from rog.app.models.obligation import Obligation
from rog.app.models.section import Section
from rog.app.services.relationship_detector import RelationshipDetector

logger = logging.getLogger(__name__)

MANDATORY_KEYWORDS = ("must", "shall", "required to", "is obligated to")
RESPONSIBLE_PARTIES = ("company", "employer", "organization", "license holder")
PENALTY_KEYWORDS = ("penalty", "fine", "punishable", "liable to")

_DEADLINE_PATTERNS = (
    re.compile(r"\bwithin\s+\d+\s+days?\b", re.IGNORECASE),
    re.compile(r"\bbefore\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\bbefore\s+[A-Za-z]+\s+\d{1,2},?\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"\bannually\b", re.IGNORECASE),
    re.compile(r"\bmonthly\b", re.IGNORECASE),
    re.compile(r"\bquarterly\b", re.IGNORECASE),
)

_CONDITION_PATTERN = re.compile(r"\b(if|provided that|subject to)\b(.+?)(?:\.|;|$)", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[\.;])\s+|\n+")


@dataclass(slots=True)
class ObligationCandidate:
    action_text: str
    responsible_party: str | None
    deadline_text: str | None
    penalty_text: str | None
    mandatory_flag: bool
    condition_text: str | None


def _contains_mandatory(text: str) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in MANDATORY_KEYWORDS)


def detect_deadline_text(text: str) -> str | None:
    for pattern in _DEADLINE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def detect_penalty_text(text: str) -> str | None:
    lowered = text.lower()
    first_idx: int | None = None
    for key in PENALTY_KEYWORDS:
        idx = lowered.find(key)
        if idx == -1:
            continue
        if first_idx is None or idx < first_idx:
            first_idx = idx
    if first_idx is not None:
        return text[first_idx:].strip()[:255]
    return None


def detect_responsible_party(text: str) -> str | None:
    lowered = text.lower()
    for party in RESPONSIBLE_PARTIES:
        if party in lowered:
            return party
    return None


def detect_condition_text(text: str) -> str | None:
    match = _CONDITION_PATTERN.search(text)
    if not match:
        return None
    return match.group(0).strip()


def extract_obligations_from_text(text: str) -> list[ObligationCandidate]:
    chunks = [c.strip() for c in _SENTENCE_SPLIT.split(text) if c.strip()]
    candidates: list[ObligationCandidate] = []
    for chunk in chunks:
        mandatory = _contains_mandatory(chunk)
        deadline = detect_deadline_text(chunk)
        penalty = detect_penalty_text(chunk)
        party = detect_responsible_party(chunk)

        if not mandatory and not deadline and not penalty:
            continue

        candidates.append(
            ObligationCandidate(
                action_text=chunk,
                responsible_party=party,
                deadline_text=deadline,
                penalty_text=penalty,
                mandatory_flag=mandatory,
                condition_text=detect_condition_text(chunk),
            )
        )
    return candidates


class ObligationExtractor:
    def __init__(self, db: Session) -> None:
        self.db = db

    def extract_for_sections(self, *, section_ids: list[uuid.UUID]) -> int:
        logger.info("obligation_extraction_start sections=%s", len(section_ids))
        created = 0
        try:
            sections = self.db.query(Section).filter(Section.id.in_(section_ids)).all()
            created_obligation_ids: list[uuid.UUID] = []
            for section in sections:
                candidates = extract_obligations_from_text(section.content or "")
                for cand in candidates:
                    obligation = Obligation(
                        section_id=section.id,
                        action_text=cand.action_text,
                        responsible_party=cand.responsible_party,
                        deadline_text=cand.deadline_text,
                        penalty_text=cand.penalty_text,
                        mandatory_flag=cand.mandatory_flag,
                        condition_text=cand.condition_text,
                    )
                    self.db.add(obligation)
                    self.db.flush()
                    created_obligation_ids.append(obligation.id)
                    created += 1
                    logger.info("obligation_detected section_id=%s mandatory=%s", section.id, cand.mandatory_flag)

            relationship_detector = RelationshipDetector(self.db)
            relationship_detector.detect_and_store(obligation_ids=created_obligation_ids)
            return created
        except Exception:
            logger.exception("obligation_extraction_failure")
            raise

