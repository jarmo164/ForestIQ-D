"""Versioned cache helpers for organization-scoped vector tiles."""

from __future__ import annotations

from hashlib import sha256
from typing import Iterable

from django.conf import settings
from django.core.cache import cache

_CACHE_PREFIX = "forestiq:mvt"
_VERSION_KEY_PREFIX = f"{_CACHE_PREFIX}:version"


def _normalise_layer(layer: str) -> str:
    """Return the known cache namespace segment for a vector tile layer."""

    return layer.strip().lower()


def tile_cache_version(organization_id: str, layer: str) -> int:
    """Return the current monotonically increasing tile-cache version."""

    key = f"{_VERSION_KEY_PREFIX}:{organization_id}:{_normalise_layer(layer)}"
    value = cache.get(key)
    return int(value) if value is not None else 1


def vector_tile_cache_key(
    *,
    organization_id: str,
    layer: str,
    z: int,
    x: int,
    y: int,
    query_fingerprint: str,
) -> str:
    """Create a bounded cache key that cannot collide across tenants or filters."""

    version = tile_cache_version(organization_id, layer)
    digest = sha256(query_fingerprint.encode("utf-8")).hexdigest()[:16]
    return f"{_CACHE_PREFIX}:tile:{organization_id}:{_normalise_layer(layer)}:v{version}:{z}:{x}:{y}:{digest}"


def get_cached_vector_tile(key: str) -> bytes | None:
    """Read a vector-tile payload only when the cached value is a byte payload."""

    value = cache.get(key)
    return bytes(value) if isinstance(value, (bytes, bytearray)) else None


def cache_vector_tile(key: str, payload: bytes) -> None:
    """Cache a tile for the configured, deliberately short private-cache interval."""

    cache.set(key, payload, timeout=settings.FORESTIQ_MVT_CACHE_TTL_SECONDS)


def invalidate_vector_tiles(organization_id: str, layers: Iterable[str] = ("cadastres", "subparts", "registry")) -> None:
    """Bump layer versions so old tile entries become immediately unreachable.

    Versioning avoids Redis wildcard deletes and keeps the invalidation cost fixed even
    when a tenant has many cached tiles. Expired entries are removed by their regular TTL.
    """

    for layer in layers:
        key = f"{_VERSION_KEY_PREFIX}:{organization_id}:{_normalise_layer(layer)}"
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 2, timeout=None)
