from __future__ import annotations

import uuid

from rog.app.models.compliance_status import ComplianceStatus
from rog.app.models.obligation import Obligation
from rog.app.services.compliance_matcher import (
    ComplianceMatcher,
    RISK_CRITICAL,
    RISK_LOW,
    STATUS_COMPLIANT,
    _compute_risk,
)


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


def test_compliance_matching() -> None:
    obligation = Obligation(
        id=uuid.uuid4(),
        section_id=uuid.uuid4(),
        action_text="Company shall maintain statutory records monthly.",
        mandatory_flag=True,
    )

    class FakeDB:
        def __init__(self):
            self.added = []

        def scalars(self, _stmt):
            return _ScalarResult([obligation])

        def scalar(self, _stmt):
            return None

        def add(self, obj):
            self.added.append(obj)

    matcher = ComplianceMatcher(FakeDB())  # type: ignore[arg-type]
    matcher._extract_document_text = lambda **_: "The company shall maintain statutory records monthly."  # type: ignore[method-assign]
    checked = matcher.match_company_document(company_id=uuid.uuid4(), file_path="x.pdf", file_type="pdf")

    assert checked == 1
    assert len(matcher.db.added) == 1
    status = matcher.db.added[0]
    assert isinstance(status, ComplianceStatus)
    assert status.status == STATUS_COMPLIANT


def test_risk_scoring() -> None:
    low = Obligation(id=uuid.uuid4(), section_id=uuid.uuid4(), action_text="Keep records.", mandatory_flag=False)
    critical = Obligation(
        id=uuid.uuid4(),
        section_id=uuid.uuid4(),
        action_text="Must file.",
        mandatory_flag=True,
        deadline_text="within 30 days",
        penalty_text="penalty up to INR 1,00,000",
    )

    assert _compute_risk(low) == RISK_LOW
    assert _compute_risk(critical) == RISK_CRITICAL

