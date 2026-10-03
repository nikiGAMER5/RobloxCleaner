"""Logging configuration and utility for Roblox Cleaner."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from app.utils.helpers import get_app_dir

LOGGER_NAME = "RobloxCleaner"


def setup_logger(log_level: int = logging.INFO) -> logging.Logger:
    """Set up and configure the application logger with rotating file and console handlers.

    Returns:
        The configured logger instance.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(log_level)
    logger.propagate = False

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    log_dir = get_app_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "roblox_cleaner.log"

    try:
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    except Exception as exc:
        print(f"Warning: Failed to setup file logger: {exc}")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the active application logger."""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        return setup_logger()
    return logger


def get_log_file_path() -> Path:
    """Get the path to the current log file."""
    return get_app_dir() / "logs" / "roblox_cleaner.log"


def read_recent_logs(max_lines: int = 200) -> str:
    """Read the most recent lines from the log file."""
    log_file = get_log_file_path()
    if not log_file.exists():
        return "Keine Logdatei vorhanden."

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except Exception as exc:
        return f"Fehler beim Lesen des Logfiles: {exc}"
