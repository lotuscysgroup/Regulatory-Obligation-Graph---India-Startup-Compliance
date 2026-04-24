from __future__ import annotations

import uuid
from datetime import date

from rog.app.models.compliance_status import ComplianceStatus
from rog.app.models.obligation import Obligation
from rog.app.services.alert_generator import ALERT_OVERDUE, ALERT_UPCOMING, AlertGenerator
from rog.app.services.compliance_matcher import RISK_CRITICAL
from rog.app.services.deadline_calculator import DeadlineCalculator


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


def test_deadline_calculation() -> None:
    ref = date(2026, 1, 1)
    due = DeadlineCalculator.calculate_due_date("within 7 days", reference_date=ref)
    assert due == date(2026, 1, 8)


def test_alert_generation() -> None:
    company_id = uuid.uuid4()
    obligation_id = uuid.uuid4()
    status = ComplianceStatus(company_id=company_id, obligation_id=obligation_id, status="NON_COMPLIANT", risk_level=RISK_CRITICAL)
    obligation = Obligation(
        id=obligation_id,
        section_id=uuid.uuid4(),
        action_text="Company must file return.",
        deadline_text="within 7 days",
        penalty_text="penalty applies",
        mandatory_flag=True,
    )

    class FakeDB:
        def scalars(self, _stmt):
            return _ScalarResult([status])

        def scalar(self, _stmt):
            return obligation

    created: list[str] = []
    gen = AlertGenerator(FakeDB())  # type: ignore[arg-type]

    def _record(**kwargs):
        created.append(kwargs["alert_type"])
        return True

    gen._create_alert_if_missing = _record  # type: ignore[method-assign]
    count = gen.run_for_company(company_id, reference_date=date(2026, 1, 1))

    assert count >= 2
    assert ALERT_UPCOMING in created


def test_overdue_detection() -> None:
    company_id = uuid.uuid4()
    obligation_id = uuid.uuid4()
    status = ComplianceStatus(company_id=company_id, obligation_id=obligation_id, status="NON_COMPLIANT", risk_level="LOW")
    obligation = Obligation(
        id=obligation_id,
        section_id=uuid.uuid4(),
        action_text="Employer shall comply.",
        deadline_text="before 01/01/2026",
        mandatory_flag=True,
    )

    class FakeDB:
        def scalars(self, _stmt):
            return _ScalarResult([status])

        def scalar(self, _stmt):
            return obligation

    created: list[str] = []
    gen = AlertGenerator(FakeDB())  # type: ignore[arg-type]
    gen._create_alert_if_missing = lambda **kwargs: created.append(kwargs["alert_type"]) or True  # type: ignore[method-assign]
    gen.run_for_company(company_id, reference_date=date(2026, 1, 3))

    assert ALERT_OVERDUE in created

