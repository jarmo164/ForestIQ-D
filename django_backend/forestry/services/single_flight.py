"""Redis-backed single-flight locks for externally sourced synchronization work."""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import Final

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

_RELEASE_IF_OWNED: Final = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""

_CLAIM_QUEUED_OR_EXPIRED_LOCK: Final = """
local current = redis.call('get', KEYS[1])
if current == ARGV[1] then
    redis.call('set', KEYS[1], ARGV[2], 'EX', ARGV[3])
    return 1
end
if not current then
    local acquired = redis.call('set', KEYS[1], ARGV[2], 'NX', 'EX', ARGV[3])
    return acquired and 1 or 0
end
return 0
"""


class SingleFlightLockUnavailable(ConnectionError):
    """Raised when Redis is unavailable and exclusivity therefore cannot be guaranteed."""


@dataclass
class SingleFlightLock:
    """A token-owned Redis lock for one tenant-scoped synchronization activity.

    A dispatcher first stores its random token as a queued reservation. The
    worker atomically exchanges it for a running token, preventing duplicate
    Celery deliveries from performing the same writes. The TTL recovers from a
    stopped dispatcher or worker without ever deleting a newer worker's key.
    """

    key: str
    ttl_seconds: int
    token: str
    owned_value: str = ""

    @classmethod
    def for_sync(cls, task_name: str, organization_id: str, scope: str = "") -> "SingleFlightLock":
        parts = ["forestiq", "single-flight", "v1", task_name, str(organization_id)]
        if scope:
            parts.append(scope)
        return cls(
            key=":".join(parts),
            ttl_seconds=settings.FORESTIQ_SINGLE_FLIGHT_LOCK_TTL_SECONDS,
            token=secrets.token_urlsafe(24),
        )

    @property
    def client(self):
        return redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)

    def acquire(self) -> bool:
        """Acquire a lock immediately for work that begins in this process."""

        try:
            acquired = bool(self.client.set(self.key, self.token, nx=True, ex=self.ttl_seconds))
        except redis.RedisError as exc:
            raise SingleFlightLockUnavailable("Redis is unavailable; synchronization was not started.") from exc
        if acquired:
            self.owned_value = self.token
        return acquired

    def claim_queued_or_recover(self) -> bool:
        """Claim this dispatcher's queued lock, or recover only after its TTL.

        A successful claim changes the Redis value to a distinct running token.
        Another delivery holding the old dispatch token therefore cannot enter
        the critical section. If the queued reservation expired before a worker
        began, this token may recover the key only when no newer owner exists.
        """

        running_value = f"running:{self.token}"
        try:
            claimed = bool(
                self.client.eval(
                    _CLAIM_QUEUED_OR_EXPIRED_LOCK,
                    1,
                    self.key,
                    self.token,
                    running_value,
                    self.ttl_seconds,
                )
            )
        except redis.RedisError as exc:
            raise SingleFlightLockUnavailable("Redis is unavailable; synchronization ownership cannot be verified.") from exc
        if claimed:
            self.owned_value = running_value
        return claimed

    def release(self) -> None:
        """Release the key only if this lock's token is still the stored owner."""

        if not self.owned_value:
            return
        try:
            self.client.eval(_RELEASE_IF_OWNED, 1, self.key, self.owned_value)
        except redis.RedisError:
            # A failed release cannot risk deleting a recovered worker's lock.
            # The configured TTL remains the safe recovery mechanism.
            logger.warning("Could not release single-flight lock %s; waiting for its TTL.", self.key, exc_info=True)


def recover_or_acquire(lock: SingleFlightLock) -> bool:
    """Acquire an immediate-execution lock, returning false when another run owns it."""

    return lock.acquire()
