"""Bounded client for Weasel ownership-change deltas."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
import time
from typing import Any

import requests
from django.conf import settings


class WeaselClientError(RuntimeError):
    """The Weasel delta endpoint could not be safely consumed."""


@dataclass(frozen=True)
class WeaselPolicy:
    page_size: int
    max_events: int
    max_payload_bytes: int
    max_retries: int
    retry_backoff_seconds: float

    @classmethod
    def from_settings(cls) -> "WeaselPolicy":
        return cls(
            page_size=settings.FORESTIQ_WEASEL_PAGE_SIZE,
            max_events=settings.FORESTIQ_WEASEL_MAX_EVENTS,
            max_payload_bytes=settings.FORESTIQ_WEASEL_MAX_PAYLOAD_BYTES,
            max_retries=settings.FORESTIQ_WEASEL_MAX_RETRIES,
            retry_backoff_seconds=settings.FORESTIQ_WEASEL_RETRY_BACKOFF_SECONDS,
        )


@dataclass(frozen=True)
class WeaselChangePage:
    events: list[dict[str, Any]]
    next_cursor: str | None


class WeaselOwnershipClient:
    """Read cursor-based ownership-change pages with bounded network behavior."""

    _RETRYABLE_STATUS_CODES = frozenset((429, 500, 502, 503, 504))

    def __init__(
        self,
        policy: WeaselPolicy | None = None,
        *,
        request_get: Callable[..., requests.Response] = requests.get,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.policy = policy or WeaselPolicy.from_settings()
        self.request_get = request_get
        self.sleep = sleep

    def _url(self) -> str:
        base_url = settings.WEASEL_API_URL.rstrip("/")
        path = settings.FORESTIQ_WEASEL_CHANGES_PATH.strip()
        if not base_url or not settings.WEASEL_API_TOKEN:
            raise WeaselClientError("Weasel API URL and token must be configured before synchronization.")
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base_url}{path}"

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.WEASEL_API_TOKEN}",
            "User-Agent": settings.FORESTIQ_SYNC_USER_AGENT,
        }

    def _payload_size(self, response: requests.Response, payload: dict[str, Any]) -> int:
        content_length = str(getattr(response, "headers", {}).get("Content-Length", ""))
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = 0
        if declared_size > self.policy.max_payload_bytes:
            raise WeaselClientError(f"Weasel response exceeds the {self.policy.max_payload_bytes}-byte payload policy.")
        content = getattr(response, "content", None)
        return len(content) if isinstance(content, (bytes, bytearray)) else len(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    def ownership_change_page(self, cursor: str | None = None) -> WeaselChangePage:
        if self.policy.page_size < 1 or self.policy.page_size > self.policy.max_events:
            raise WeaselClientError("Weasel page size must be positive and not exceed the event budget.")
        params: dict[str, Any] = {"limit": self.policy.page_size}
        if cursor:
            params["cursor"] = cursor
        response: requests.Response | None = None
        for attempt in range(self.policy.max_retries + 1):
            try:
                response = self.request_get(
                    self._url(), params=params, headers=self._headers(), timeout=settings.FORESTIQ_SYNC_HTTP_TIMEOUT_SECONDS
                )
                if response.status_code in self._RETRYABLE_STATUS_CODES and attempt < self.policy.max_retries:
                    self.sleep(self.policy.retry_backoff_seconds * (2**attempt))
                    continue
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                if attempt == self.policy.max_retries:
                    raise WeaselClientError(f"Weasel request failed after {attempt + 1} attempt(s): {exc}") from exc
                self.sleep(self.policy.retry_backoff_seconds * (2**attempt))
        else:  # pragma: no cover - loop either raises or returns a response
            raise WeaselClientError("Weasel request did not produce a response.")
        try:
            payload = response.json()
        except ValueError as exc:
            raise WeaselClientError("Weasel returned non-JSON data.") from exc
        if not isinstance(payload, dict):
            raise WeaselClientError("Weasel returned an invalid delta page.")
        if self._payload_size(response, payload) > self.policy.max_payload_bytes:
            raise WeaselClientError(f"Weasel response exceeds the {self.policy.max_payload_bytes}-byte payload policy.")
        events = payload.get("events", payload.get("items", []))
        if not isinstance(events, list) or any(not isinstance(event, dict) for event in events):
            raise WeaselClientError("Weasel delta page must contain an events array.")
        if len(events) > self.policy.page_size:
            raise WeaselClientError("Weasel delta page exceeds the requested limit.")
        next_cursor = payload.get("nextCursor", payload.get("next_cursor"))
        if next_cursor is not None and not isinstance(next_cursor, (str, int)):
            raise WeaselClientError("Weasel next cursor must be text or numeric.")
        return WeaselChangePage(events=events, next_cursor=str(next_cursor) if next_cursor not in (None, "") else None)
