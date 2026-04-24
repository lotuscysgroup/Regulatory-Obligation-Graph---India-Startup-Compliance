from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from rog.app.models.alert import Alert
from rog.app.models.compliance_status import ComplianceStatus
from rog.app.models.obligation import Obligation
from rog.app.services.compliance_matcher import RISK_CRITICAL, RISK_HIGH
from rog.app.services.deadline_calculator import DeadlineCalculator

logger = logging.getLogger(__name__)

ALERT_UPCOMING = "UPCOMING"
ALERT_OVERDUE = "OVERDUE"
ALERT_HIGH_RISK = "HIGH_RISK"
ALERT_PENALTY_WARNING = "PENALTY_WARNING"

STATUS_ACTIVE = "ACTIVE"
STATUS_RESOLVED = "RESOLVED"
STATUS_DISMISSED = "DISMISSED"


class AlertGenerator:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _create_alert_if_missing(
        self,
        *,
        company_id: uuid.UUID,
        obligation_id: uuid.UUID,
        alert_type: str,
        message: str,
        due_date: date | None,
    ) -> bool:
        existing = self.db.scalar(
            select(Alert).where(
                Alert.company_id == company_id,
                Alert.obligation_id == obligation_id,
                Alert.alert_type == alert_type,
                Alert.status == STATUS_ACTIVE,
            )
        )
        if existing is not None:
            return False
        self.db.add(
            Alert(
                company_id=company_id,
                obligation_id=obligation_id,
                alert_type=alert_type,
                message=message,
                due_date=due_date,
                status=STATUS_ACTIVE,
            )
        )
        logger.info(
            "alert_created company_id=%s obligation_id=%s type=%s",
            company_id,
            obligation_id,
            alert_type,
        )
        return True

    def run_for_company(self, company_id: uuid.UUID, *, reference_date: date | None = None) -> int:
        logger.info("alert_generation_start company_id=%s", company_id)
        today = reference_date or date.today()
        created = 0
        try:
            statuses = self.db.scalars(select(ComplianceStatus).where(ComplianceStatus.company_id == company_id)).all()
            for status in statuses:
                obligation = self.db.scalar(select(Obligation).where(Obligation.id == status.obligation_id))
                if obligation is None:
                    continue

                due_date = DeadlineCalculator.calculate_due_date(obligation.deadline_text, reference_date=today)
                if due_date is not None:
                    days_left = (due_date - today).days
                    if days_left in (7, 3, 1):
                        created += int(
                            self._create_alert_if_missing(
                                company_id=company_id,
                                obligation_id=obligation.id,
                                alert_type=ALERT_UPCOMING,
                                message=f"Obligation due in {days_left} day(s).",
                                due_date=due_date,
                            )
                        )
                    elif days_left < 0:
                        created += int(
                            self._create_alert_if_missing(
                                company_id=company_id,
                                obligation_id=obligation.id,
                                alert_type=ALERT_OVERDUE,
                                message="Obligation is overdue.",
                                due_date=due_date,
                            )
                        )

                if status.risk_level in (RISK_HIGH, RISK_CRITICAL):
                    created += int(
                        self._create_alert_if_missing(
                            company_id=company_id,
                            obligation_id=obligation.id,
                            alert_type=ALERT_HIGH_RISK,
                            message=f"High compliance risk detected: {status.risk_level}.",
                            due_date=due_date,
                        )
                    )

                if obligation.penalty_text:
                    created += int(
                        self._create_alert_if_missing(
                            company_id=company_id,
                            obligation_id=obligation.id,
                            alert_type=ALERT_PENALTY_WARNING,
                            message="Penalty warning tied to this obligation.",
                            due_date=due_date,
                        )
                    )
            return created
        except Exception:
            logger.exception("alert_delivery_failure company_id=%s", company_id)
            raise

    def run_daily_checks(self, *, reference_date: date | None = None) -> int:
        total = 0
        company_ids = self.db.scalars(select(ComplianceStatus.company_id).distinct()).all()
        for company_id in company_ids:
            total += self.run_for_company(company_id, reference_date=reference_date)
        return total

    def get_company_alerts(self, company_id: uuid.UUID) -> list[Alert]:
        return self.db.scalars(select(Alert).where(Alert.company_id == company_id).order_by(Alert.created_at.desc())).all()

    def get_active_alerts(self, company_id: uuid.UUID) -> list[Alert]:
        return self.db.scalars(
            select(Alert).where(Alert.company_id == company_id, Alert.status == STATUS_ACTIVE).order_by(Alert.created_at.desc())
        ).all()

    def get_overdue_alerts(self, company_id: uuid.UUID) -> list[Alert]:
        return self.db.scalars(
            select(Alert).where(
                Alert.company_id == company_id,
                Alert.alert_type == ALERT_OVERDUE,
                Alert.status == STATUS_ACTIVE,
            )
        ).all()

