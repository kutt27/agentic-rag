"""
Structured logging configuration with JSON output for production.

Uses a simple formatter that outputs structured log records.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    """Format log records as JSON for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "tool_name"):
            log_entry["tool_name"] = record.tool_name

        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO", log_file: Path | None = None) -> None:
    """Setup structured logging for the application."""

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.setLevel(numeric_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JsonFormatter())
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name."""
    return logging.getLogger(name)