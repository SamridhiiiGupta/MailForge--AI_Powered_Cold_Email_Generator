"""
Structured logging utility.
Single logger setup used across all modules.
Log level controlled via LOG_LEVEL env variable.
"""

import logging
import os
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger with consistent formatting.
    All loggers share the same level set by LOG_LEVEL env var.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level, logging.INFO)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Avoid duplicate handlers on re-import

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
