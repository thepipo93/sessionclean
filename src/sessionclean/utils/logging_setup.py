"""Centralized logging configuration for SessionClean."""

import logging
import sys

from sessionclean.constants import APP_DIR, LOG_PATH


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the application-wide logger.

    Logs go to both a file and stderr.
    The log file is stored at ~/.sessionclean/sessionclean.log
    """
    APP_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("sessionclean")
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler (rotating would be nice later, simple for MVP)
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
