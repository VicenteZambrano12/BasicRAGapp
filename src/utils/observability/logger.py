"""Centralized structured logging: JSON formatting + request correlation IDs.

Call ``configure_logging()`` once at process startup (see ``src/api/app.py``).
Every module should keep using ``logging.getLogger(__name__)`` as before -
the correlation id and JSON formatting are applied globally via the root
logger's handler, so no per-module changes are required.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Optional

# Attributes present on every stdlib LogRecord; anything else set via
# `extra={...}` is treated as a custom field and included in the JSON output.
_STANDARD_RECORD_ATTRS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message", "correlation_id",
}

_correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Return the correlation id bound to the current request context, if any."""
    return _correlation_id_var.get()


def set_correlation_id(correlation_id: Optional[str] = None) -> tuple[str, Token]:
    """Bind a correlation id to the current context, generating one if omitted.

    Returns the id and a token that must be passed to ``reset_correlation_id``
    once the request finishes, so the contextvar doesn't leak across requests.
    """
    value = correlation_id or str(uuid.uuid4())
    token = _correlation_id_var.set(value)
    return value, token


def reset_correlation_id(token: Token) -> None:
    """Undo a previous ``set_correlation_id`` call."""
    _correlation_id_var.reset(token)


class CorrelationIdFilter(logging.Filter):
    """Injects the current request's correlation id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        return True


class JSONFormatter(logging.Formatter):
    """Renders log records as single-line JSON for cloud log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }

        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS and key not in payload:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    """Human-friendly formatter for local development."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(correlation_id)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )


_configured = False


def configure_logging(level: Optional[str] = None, json_logs: Optional[bool] = None) -> None:
    """Configure the root logger once at process startup.

    - ``level``: overrides the ``LOG_LEVEL`` env var (default ``INFO``).
    - ``json_logs``: overrides the ``LOG_FORMAT`` env var. JSON is used by
      default (production-friendly); set ``LOG_FORMAT=text`` for readable
      local development logs.
    """
    global _configured
    if _configured:
        return

    resolved_level = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    if json_logs is None:
        json_logs = os.environ.get("LOG_FORMAT", "json").lower() != "text"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter() if json_logs else TextFormatter())
    handler.addFilter(CorrelationIdFilter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(resolved_level)

    # Quiet down noisy third-party loggers unless explicitly raised.
    for noisy_logger in ("uvicorn.access",):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper around ``logging.getLogger`` for consistency."""
    return logging.getLogger(name)
