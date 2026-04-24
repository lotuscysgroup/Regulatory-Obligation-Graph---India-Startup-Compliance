from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FORMAT = (
    "%(asctime)s %(levelname)s "
    "%(name)s %(process)d %(threadName)s "
    "%(message)s"
)


def configure_logging(*, log_level: str, log_dir: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(log_dir, "rog.log")
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=25 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

