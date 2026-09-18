"""Bounded HTTP client shared by authorised registry adapters."""
from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from email.utils import parsedate_to_datetime
import json
import time
from typing import Any
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.utils import timezone


class AuthorizedApiError(RuntimeError):
    """An authorised provider response could not be consumed safely."""


class AuthorizedApiClient:
    RETRYABLE = frozenset((429, 500, 502, 503, 504))

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        request_get: Callable[..., requests.Response] = requests.get,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.request_get = request_get
        self.sleep = sleep

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": settings.FORESTIQ_SYNC_USER_AGENT,
        }

    def _retry_delay(self, attempt: int, response: requests.Response | None) -> float:
        retry_after = str(getattr(response, "headers", {}).get("Retry-After", "")).strip()
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    parsed = parsedate_to_datetime(retry_after)
                    if parsed.tzinfo is None:
                        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
                    return max(0.0, (parsed - timezone.now()).total_seconds())
                except (TypeError, ValueError, OverflowError):
                    pass
        return settings.FORESTIQ_AUTH_API_RETRY_BACKOFF_SECONDS * (2**attempt)

    def get_pages(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        records_key: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        if not self.base_url or not self.token:
            raise AuthorizedApiError("Provider URL and token must be configured before synchronization.")
        url = urljoin(f"{self.base_url}/", path.lstrip("/"))
        query = dict(params or {})
        seen: set[str] = set()
        for _page_number in range(settings.FORESTIQ_AUTH_API_MAX_PAGES):
            response: requests.Response | None = None
            for attempt in range(settings.FORESTIQ_AUTH_API_MAX_RETRIES + 1):
                try:
                    response = self.request_get(
                        url,
                        params=query or None,
                        headers=self._headers(),
                        timeout=settings.FORESTIQ_SYNC_HTTP_TIMEOUT_SECONDS,
                    )
                    if response.status_code in self.RETRYABLE and attempt < settings.FORESTIQ_AUTH_API_MAX_RETRIES:
                        self.sleep(self._retry_delay(attempt, response))
                        continue
                    response.raise_for_status()
                    break
                except requests.RequestException as exc:
                    if attempt == settings.FORESTIQ_AUTH_API_MAX_RETRIES:
                        raise AuthorizedApiError(f"Provider request failed after {attempt + 1} attempt(s): {exc}") from exc
                    self.sleep(self._retry_delay(attempt, response))
            try:
                payload = response.json()
            except ValueError as exc:
                raise AuthorizedApiError("Provider returned non-JSON data.") from exc
            if not isinstance(payload, dict):
                raise AuthorizedApiError("Provider response must be a JSON object.")
            response_content = getattr(response, "content", None)
            encoded_payload = json.dumps(payload, separators=(",", ":")).encode()
            payload_size = len(response_content) if isinstance(response_content, (bytes, bytearray)) else len(encoded_payload)
            if payload_size > settings.FORESTIQ_AUTH_API_MAX_PAYLOAD_BYTES:
                raise AuthorizedApiError("Provider response exceeds the configured payload limit.")
            if records_key is not None:
                records = payload.get(records_key, [])
                if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
                    raise AuthorizedApiError(f"Provider response field {records_key!r} must be an object array.")
            yield payload
            next_value = payload.get("next") or payload.get("nextUrl") or payload.get("next_cursor") or payload.get("nextCursor")
            if next_value in (None, ""):
                return
            marker = str(next_value)
            if marker in seen:
                raise AuthorizedApiError("Provider pagination cursor repeated.")
            seen.add(marker)
            if marker.startswith(("http://", "https://")):
                url = marker
                query = {}
            else:
                query = {**query, "cursor": marker}
        raise AuthorizedApiError("Provider pagination exceeded the configured page limit.")
