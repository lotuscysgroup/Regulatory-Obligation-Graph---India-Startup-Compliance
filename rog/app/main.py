from __future__ import annotations

import logging

from fastapi import FastAPI

from rog.app.api.health import router as health_router
from rog.app.api.v1.router import router as v1_router
from rog.app.core.config import get_settings
from rog.app.core.database import init_engine
from rog.app.core.logging import configure_logging
from rog.app.core.redis import init_redis


def create_app() -> FastAPI:
    app = FastAPI(
        title="Regulatory Obligation Graph (ROG)",
        version="0.1.0",
    )

    @app.on_event("startup")
    def _startup() -> None:
        settings = get_settings()
        app.state.settings = settings

        configure_logging(log_level=settings.log_level, log_dir=settings.log_dir)
        init_engine(settings.database_url)
        init_redis(settings.redis_url)

        logging.getLogger(__name__).info("ROG startup complete")

    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()
