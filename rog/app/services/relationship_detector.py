from __future__ import annotations

import logging
import re
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from rog.app.models.obligation import Obligation
from rog.app.models.obligation_relationship import ObligationRelationship
from rog.app.models.section import Section

logger = logging.getLogger(__name__)

SUPPORTED_RELATIONSHIP_TYPES = {
    "depends_on",
    "conflicts_with",
    "overrides",
    "requires",
    "references",
}

_PHRASE_TO_TYPE: tuple[tuple[str, str], ...] = (
    ("depends on", "depends_on"),
    ("requires", "requires"),
    ("subject to", "depends_on"),
    ("unless", "conflicts_with"),
    ("notwithstanding", "overrides"),
    ("in accordance with", "references"),
    ("as per section", "references"),
)
_SECTION_REF_RE = re.compile(r"\bsection\s+(\d+(?:\.\d+)*)\b", re.IGNORECASE)


def _detect_relationship_type(text: str) -> str | None:
    lowered = text.lower()
    for phrase, rel_type in _PHRASE_TO_TYPE:
        if phrase in lowered:
            return rel_type
    return None


class RelationshipDetector:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _find_target_obligation(self, source: Obligation, source_section: Section) -> Obligation | None:
        ref_match = _SECTION_REF_RE.search(source.action_text)
        base_query = (
            select(Obligation, Section)
            .join(Section, Section.id == Obligation.section_id)
            .where(
                Section.regulation_version_id == source_section.regulation_version_id,
                Obligation.id != source.id,
            )
            .order_by(Section.order_index.asc(), Obligation.created_at.asc())
        )
        rows = self.db.execute(base_query).all()
        if not rows:
            return None

        if ref_match:
            section_ref = ref_match.group(1)
            for candidate, candidate_section in rows:
                if (candidate_section.section_number or "").startswith(section_ref):
                    return candidate

        # Fallback: use the nearest neighboring obligation in the same version.
        return rows[0][0]

    def detect_and_store(self, *, obligation_ids: list[uuid.UUID]) -> int:
        logger.info("relationship_detection_start obligations=%s", len(obligation_ids))
        created = 0
        try:
            if not obligation_ids:
                return 0

            obligations = self.db.scalars(
                select(Obligation).where(Obligation.id.in_(obligation_ids)).order_by(Obligation.created_at.asc())
            ).all()

            for obligation in obligations:
                rel_type = _detect_relationship_type(obligation.action_text)
                if rel_type is None:
                    continue

                source_section = self.db.scalar(select(Section).where(Section.id == obligation.section_id))
                if source_section is None:
                    continue

                target = self._find_target_obligation(obligation, source_section)
                if target is None:
                    continue

                exists = self.db.scalar(
                    select(ObligationRelationship).where(
                        ObligationRelationship.source_obligation_id == obligation.id,
                        ObligationRelationship.target_obligation_id == target.id,
                        ObligationRelationship.relationship_type == rel_type,
                    )
                )
                if exists is not None:
                    continue

                relationship = ObligationRelationship(
                    source_obligation_id=obligation.id,
                    target_obligation_id=target.id,
                    relationship_type=rel_type,
                    confidence_score=0.8 if "section" in obligation.action_text.lower() else 0.6,
                )
                self.db.add(relationship)
                created += 1
                logger.info(
                    "relationship_created source=%s target=%s type=%s",
                    obligation.id,
                    target.id,
                    rel_type,
                )

            return created
        except Exception:
            logger.exception("relationship_detection_failure")
            raise

    def get_dependencies(self, obligation_id: uuid.UUID) -> list[ObligationRelationship]:
        return self.db.scalars(
            select(ObligationRelationship).where(
                ObligationRelationship.source_obligation_id == obligation_id,
                ObligationRelationship.relationship_type.in_(("depends_on", "requires", "references")),
            )
        ).all()

    def get_dependents(self, obligation_id: uuid.UUID) -> list[ObligationRelationship]:
        return self.db.scalars(
            select(ObligationRelationship).where(
                ObligationRelationship.target_obligation_id == obligation_id,
                ObligationRelationship.relationship_type.in_(("depends_on", "requires", "references")),
            )
        ).all()

    def get_conflicts(self, obligation_id: uuid.UUID) -> list[ObligationRelationship]:
        return self.db.scalars(
            select(ObligationRelationship).where(
                ObligationRelationship.relationship_type == "conflicts_with",
                or_(
                    ObligationRelationship.source_obligation_id == obligation_id,
                    ObligationRelationship.target_obligation_id == obligation_id,
                ),
            )
        ).all()

