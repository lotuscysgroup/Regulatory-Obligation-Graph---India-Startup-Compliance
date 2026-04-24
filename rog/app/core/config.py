from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    """
    Load environment variables from .env (if present).

    - In Docker Compose we mount the repo into /app, so /app/.env is typical.
    - For local dev, repo root .env is typical.
    """
    cwd = Path.cwd()
    candidates = [
        cwd / ".env",
        cwd.parent / ".env",
        Path("/app/.env"),
    ]
    for p in candidates:
        if p.exists():
            load_dotenv(dotenv_path=p, override=False)
            break


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    database_url: str
    redis_url: str
    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    storage_dir: str
    max_upload_mb: int
    log_level: str
    log_dir: str


def get_settings() -> Settings:
    _load_env()

    environment = os.getenv("ENVIRONMENT", "local")
    database_url = os.getenv("DATABASE_URL", "").strip()
    redis_url = os.getenv("REDIS_URL", "").strip()
    secret_key = os.getenv("SECRET_KEY", "").strip()
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256").strip()
    access_token_expire_minutes_raw = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60").strip()
    storage_dir = os.getenv("STORAGE_DIR", "storage").strip()
    max_upload_mb_raw = os.getenv("MAX_UPLOAD_MB", "25").strip()

    if not database_url:
        raise RuntimeError("DATABASE_URL is required")
    if not redis_url:
        raise RuntimeError("REDIS_URL is required")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is required")
    if not jwt_algorithm:
        raise RuntimeError("JWT_ALGORITHM is required")

    try:
        access_token_expire_minutes = int(access_token_expire_minutes_raw)
    except ValueError as e:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer") from e

    try:
        max_upload_mb = int(max_upload_mb_raw)
    except ValueError as e:
        raise RuntimeError("MAX_UPLOAD_MB must be an integer") from e

    if max_upload_mb <= 0:
        raise RuntimeError("MAX_UPLOAD_MB must be > 0")
    if not storage_dir:
        raise RuntimeError("STORAGE_DIR is required")

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("LOG_DIR", "logs")

    return Settings(
        environment=environment,
        database_url=database_url,
        redis_url=redis_url,
        secret_key=secret_key,
        jwt_algorithm=jwt_algorithm,
        access_token_expire_minutes=access_token_expire_minutes,
        storage_dir=storage_dir,
        max_upload_mb=max_upload_mb,
        log_level=log_level,
        log_dir=log_dir,
    )

