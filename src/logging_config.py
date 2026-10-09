"""Structured, opt-in logging. Set BK_LOG_LEVEL=DEBUG to see everything."""
from __future__ import annotations

import logging
import os
import sys

_configured = False


def setup_logging() -> logging.Logger:
    global _configured
    logger = logging.getLogger("bueroknakker")
    if _configured:
        return logger

    level_name = os.environ.get("BK_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    _configured = True
    return logger
