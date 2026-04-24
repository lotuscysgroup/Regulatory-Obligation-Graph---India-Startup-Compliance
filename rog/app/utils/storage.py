from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def regulations_base_dir(storage_dir: str) -> Path:
    return Path(storage_dir) / "regulations"


def regulation_version_path(*, storage_dir: str, regulation_id: str, version: int, ext: str) -> Path:
    base = regulations_base_dir(storage_dir) / regulation_id
    ensure_dir(base)
    return base / f"{version}{ext}"

