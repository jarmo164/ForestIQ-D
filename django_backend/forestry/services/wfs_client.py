"""Bounded, retrying WFS JSON client shared by all public registry imports."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
import json
import threading
import time
from typing import Any

import requests
from django.conf import settings


class WfsClientError(RuntimeError):
    """A WFS response could not be safely imported."""


@dataclass(frozen=True)
class WfsClientPolicy:
    """Bounded transfer and retry policy for public WFS endpoints."""

    max_features: int
    max_payload_bytes: int
    max_retries: int
    retry_backoff_seconds: float
    min_request_interval_seconds: float

    @classmethod
    def from_settings(cls) -> "WfsClientPolicy":
        return cls(
            max_features=settings.FORESTIQ_WFS_MAX_FEATURES,
            max_payload_bytes=settings.FORESTIQ_WFS_MAX_PAYLOAD_BYTES,
            max_retries=settings.FORESTIQ_WFS_MAX_RETRIES,
            retry_backoff_seconds=settings.FORESTIQ_WFS_RETRY_BACKOFF_SECONDS,
            min_request_interval_seconds=settings.FORESTIQ_WFS_MIN_REQUEST_INTERVAL_SECONDS,
        )


class WfsClient:
    """Fetch GeoJSON WFS pages without unbounded retries, payloads or request rates."""

    _RETRYABLE_STATUS_CODES = frozenset((429, 500, 502, 503, 504))

    def __init__(
        self,
        policy: WfsClientPolicy | None = None,
        *,
        request_get: Callable[..., requests.Response] = requests.get,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.policy = policy or WfsClientPolicy.from_settings()
        self.request_get = request_get
        self.sleep = sleep
        self.monotonic = monotonic
        self._rate_lock = threading.Lock()
        self._next_request_at = 0.0

    def _throttle(self) -> None:
        """Space outbound attempts at the configured interval in this worker process."""

        if self.policy.min_request_interval_seconds <= 0:
            return
        with self._rate_lock:
            now = self.monotonic()
            wait = max(0.0, self._next_request_at - now)
            self._next_request_at = max(now, self._next_request_at) + self.policy.min_request_interval_seconds
        if wait:
            self.sleep(wait)

    def _retry_delay(self, attempt: int, response: requests.Response | None = None) -> float:
        """Calculate bounded exponential backoff, respecting numeric Retry-After values."""

        retry_after = ""
        if response is not None:
            retry_after = str(getattr(response, "headers", {}).get("Retry-After", ""))
        try:
            retry_after_seconds = float(retry_after)
        except (TypeError, ValueError):
            retry_after_seconds = 0.0
        return max(retry_after_seconds, self.policy.retry_backoff_seconds * (2**attempt))

    def _response_payload_size(self, response: requests.Response, payload: dict[str, Any]) -> int:
        """Measure bytes from the HTTP body where possible, otherwise serialize the JSON payload."""

        content_length = getattr(response, "headers", {}).get("Content-Length")
        if content_length:
            try:
                declared_size = int(content_length)
            except (TypeError, ValueError):
                declared_size = 0
            if declared_size > self.policy.max_payload_bytes:
                raise WfsClientError(
                    f"WFS response exceeds the {self.policy.max_payload_bytes}-byte payload policy."
                )
        content = getattr(response, "content", None)
        if isinstance(content, (bytes, bytearray)):
            return len(content)
        return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

    def feature_page(
        self,
        *,
        base_url: str,
        layer: str,
        page_size: int,
        start_index: int = 0,
        cql_filter: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch and validate one bounded WFS 2.0 GeoJSON feature page."""

        if not base_url or not layer:
            return []
        if page_size < 1 or page_size > self.policy.max_features:
            raise WfsClientError(
                f"WFS page size must be between 1 and {self.policy.max_features} features."
            )
        if start_index < 0:
            raise WfsClientError("WFS startIndex must not be negative.")

        params: dict[str, Any] = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": layer,
            "outputFormat": "application/json",
            "srsName": "EPSG:3301",
            "count": page_size,
            "startIndex": start_index,
        }
        if cql_filter:
            params["CQL_FILTER"] = cql_filter

        response: requests.Response | None = None
        for attempt in range(self.policy.max_retries + 1):
            response = None
            try:
                self._throttle()
                response = self.request_get(
                    base_url,
                    params=params,
                    headers=dict(headers or {}),
                    timeout=settings.FORESTIQ_SYNC_HTTP_TIMEOUT_SECONDS,
                )
                status_code = getattr(response, "status_code", 200)
                if isinstance(status_code, int) and status_code in self._RETRYABLE_STATUS_CODES:
                    if attempt < self.policy.max_retries:
                        self.sleep(self._retry_delay(attempt, response))
                        continue
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                status_code = getattr(response, "status_code", None)
                if isinstance(status_code, int) and status_code not in self._RETRYABLE_STATUS_CODES:
                    raise WfsClientError(f"{layer} WFS request failed without retry: {exc}") from exc
                if attempt == self.policy.max_retries:
                    raise WfsClientError(
                        f"{layer} WFS request failed after {attempt + 1} attempt(s): {exc}"
                    ) from exc
                self.sleep(self._retry_delay(attempt, response))
        else:  # pragma: no cover - loop exits through break or the exception branch
            raise WfsClientError(f"{layer} WFS request did not produce a response.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise WfsClientError(f"{layer} returned non-JSON data.") from exc
        if not isinstance(payload, dict):
            raise WfsClientError(f"{layer} returned an invalid WFS FeatureCollection.")
        payload_size = self._response_payload_size(response, payload)
        if payload_size > self.policy.max_payload_bytes:
            raise WfsClientError(
                f"{layer} returned {payload_size} bytes, exceeding the {self.policy.max_payload_bytes}-byte payload policy."
            )
        features = payload.get("features")
        if not isinstance(features, list):
            raise WfsClientError(f"{layer} returned an invalid WFS FeatureCollection.")
        if len(features) > page_size:
            raise WfsClientError(f"{layer} returned more features than the requested page size.")
        if any(not isinstance(feature, dict) for feature in features):
            raise WfsClientError(f"{layer} returned a malformed feature collection.")
        return features

    def iter_feature_pages(
        self,
        *,
        base_url: str,
        layer: str,
        page_size: int,
        cql_filter: str | None = None,
        headers: Mapping[str, str] | None = None,
        max_features: int | None = None,
        start_index: int = 0,
    ) -> Iterator[list[dict[str, Any]]]:
        """Yield consecutive WFS pages from a validated cursor within the feature budget."""

        feature_budget = self.policy.max_features if max_features is None else max_features
        if feature_budget < 1:
            raise WfsClientError("WFS feature budget must be positive.")
        if start_index < 0:
            raise WfsClientError("WFS startIndex must not be negative.")
        fetched = 0
        while True:
            requested_count = min(page_size, feature_budget - fetched)
            page = self.feature_page(
                base_url=base_url,
                layer=layer,
                page_size=requested_count,
                start_index=start_index,
                cql_filter=cql_filter,
                headers=headers,
            )
            if not page:
                return
            yield page
            fetched += len(page)
            if fetched >= feature_budget:
                raise WfsClientError(
                    f"{layer} reached the {feature_budget}-feature safety budget; narrow the WFS filter."
                )
            if len(page) < requested_count:
                return
            start_index += len(page)


def wfs_client() -> WfsClient:
    """Create a policy-backed client while retaining request patchability in importer tests."""

    return WfsClient(request_get=requests.get)
