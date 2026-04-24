from __future__ import annotations

import uuid

from rog.app.models.obligation import Obligation
from rog.app.models.obligation_relationship import ObligationRelationship
from rog.app.models.section import Section
from rog.app.services.relationship_detector import RelationshipDetector


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


def test_relationship_detection() -> None:
    section_id_1 = uuid.uuid4()
    section_id_2 = uuid.uuid4()
    obligation_1 = Obligation(id=uuid.uuid4(), section_id=section_id_1, action_text="Company shall comply as per section 2.")
    obligation_2 = Obligation(id=uuid.uuid4(), section_id=section_id_2, action_text="Organization must file return monthly.")

    section_1 = Section(id=section_id_1, regulation_version_id=uuid.uuid4(), content="s1", order_index=1, section_number="1")
    section_2 = Section(
        id=section_id_2,
        regulation_version_id=section_1.regulation_version_id,
        content="s2",
        order_index=2,
        section_number="2",
    )

    class FakeDB:
        def __init__(self):
            self.added = []
            self._scalar_count = 0

        def scalars(self, _stmt):
            return _ScalarResult([obligation_1, obligation_2])

        def scalar(self, _stmt):
            self._scalar_count += 1
            # section lookup then existing relationship lookup.
            if self._scalar_count in (1, 3):
                return section_1 if self._scalar_count == 1 else section_2
            return None

        def execute(self, _stmt):
            class _Rows:
                def all(self_inner):
                    return [(obligation_2, section_2)]

            return _Rows()

        def add(self, obj):
            self.added.append(obj)

    db = FakeDB()
    detector = RelationshipDetector(db)  # type: ignore[arg-type]
    created = detector.detect_and_store(obligation_ids=[obligation_1.id, obligation_2.id])

    assert created == 1
    assert len(db.added) == 1
    rel = db.added[0]
    assert isinstance(rel, ObligationRelationship)
    assert rel.relationship_type == "references"
    assert rel.source_obligation_id == obligation_1.id
    assert rel.target_obligation_id == obligation_2.id


def test_dependency_lookup() -> None:
    relationship = ObligationRelationship(
        id=uuid.uuid4(),
        source_obligation_id=uuid.uuid4(),
        target_obligation_id=uuid.uuid4(),
        relationship_type="depends_on",
        confidence_score=0.9,
    )

    class FakeDB:
        def scalars(self, _stmt):
            return _ScalarResult([relationship])

    db = FakeDB()
    detector = RelationshipDetector(db)  # type: ignore[arg-type]

    deps = detector.get_dependencies(relationship.source_obligation_id)
    dependents = detector.get_dependents(relationship.target_obligation_id)
    conflicts = detector.get_conflicts(relationship.source_obligation_id)

    assert len(deps) == 1
    assert len(dependents) == 1
    assert len(conflicts) == 1

