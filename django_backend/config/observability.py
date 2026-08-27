"""Safe structured logging and correlation context for HTTP and Celery execution."""

from __future__ import annotations

from collections.abc import Mapping
from contextvars import ContextVar, Token
from datetime import datetime, timezone
import json
import logging
import re
from typing import Any
from uuid import uuid4


_correlation_id: ContextVar[str] = ContextVar("forestiq_correlation_id", default="")

_SENSITIVE_KEY = re.compile(r"(?i)(authorization|cookie|password|secret|token|api[_-]?key|bearer)")
_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(authorization|cookie|password|secret|token|api[_-]?key)\s*[=:]\s*(?:bearer\s+)?[^\s,;]+"
)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_ESTONIAN_PERSONAL_CODE = re.compile(r"\b\d{11}\b")
_REQUEST_QUERY = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+([^\s?]+)\?[^\s]*", re.IGNORECASE)


def current_correlation_id() -> str:
    """Return the currently active trace identifier, if any."""

    return _correlation_id.get()


def new_correlation_id() -> str:
    """Generate an opaque client-safe correlation identifier."""

    return uuid4().hex


def set_correlation_id(value: str | None = None) -> Token[str]:
    """Bind a generated or trusted correlation identifier to this execution context."""

    return _correlation_id.set(value or new_correlation_id())


def reset_correlation_id(token: Token[str]) -> None:
    """Remove an HTTP request or Celery task trace binding after completion."""

    _correlation_id.reset(token)


def safe_correlation_id(value: object) -> str:
    """Accept only opaque client-supplied trace IDs; otherwise issue a fresh ID."""

    candidate = str(value or "").strip()
    if 8 <= len(candidate) <= 128 and re.fullmatch(r"[A-Za-z0-9._-]+", candidate):
        return candidate
    return new_correlation_id()


def redact(value: Any) -> Any:
    """Remove secrets and common personal data from structured log values."""

    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if _SENSITIVE_KEY.search(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [redact(item) for item in value]
    if isinstance(value, bytes):
        return "[REDACTED BYTES]"
    if isinstance(value, str):
        sanitized = _SENSITIVE_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
        sanitized = _REQUEST_QUERY.sub(r"\1 \2?[REDACTED]", sanitized)
        sanitized = _EMAIL.sub("[REDACTED EMAIL]", sanitized)
        return _ESTONIAN_PERSONAL_CODE.sub("[REDACTED PERSONAL CODE]", sanitized)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact(str(value))


class JsonFormatter(logging.Formatter):
    """Emit a fixed JSON schema while redacting unsafe record fields and messages."""

    _STANDARD_RECORD_FIELDS = frozenset(logging.LogRecord(None, 0, "", 0, "", (), None).__dict__) | {
        "message",
        "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
            "correlation_id": current_correlation_id() or None,
        }
        for key, value in record.__dict__.items():
            if key not in self._STANDARD_RECORD_FIELDS and not key.startswith("_"):
                payload[key] = "[REDACTED]" if _SENSITIVE_KEY.search(key) else redact(value)
        return json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":"))


class CorrelationIdFilter(logging.Filter):
    """Expose correlation ID to handlers that use non-project formatters."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = current_correlation_id() or None
        return True
