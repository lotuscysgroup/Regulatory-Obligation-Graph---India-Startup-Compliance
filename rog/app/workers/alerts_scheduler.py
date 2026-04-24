from __future__ import annotations

import asyncio
import logging

from rog.app.core.database import SessionLocal
from rog.app.services.alert_generator import AlertGenerator

logger = logging.getLogger(__name__)


async def run_daily_alert_scheduler(interval_seconds: int = 86400) -> None:
    while True:
        try:
            if SessionLocal is None:
                raise RuntimeError("SessionLocal not initialized for alert scheduler")
            db = SessionLocal()
            try:
                created = AlertGenerator(db).run_daily_checks()
                db.commit()
                logger.info("daily_alert_check_complete alerts_created=%s", created)
            finally:
                db.close()
        except Exception:
            logger.exception("daily_alert_check_failed")
        await asyncio.sleep(interval_seconds)

