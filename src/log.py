"""Minimal logging setup."""

from __future__ import annotations

import logging


def setup(level: int = logging.INFO) -> None:
    """Configure root logging once."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name)
