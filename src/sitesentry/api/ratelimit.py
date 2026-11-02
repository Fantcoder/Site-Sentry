"""Per-client rate limiter with bounded LRU memory."""

from __future__ import annotations

import time
from collections import OrderedDict


class RateLimiter:
    """Sliding-window per-client rate limiter with LRU eviction.

    Tracks request timestamps per client key (IP or API key).
    Memory is bounded by max_clients – oldest entries are evicted when full.
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: float = 60.0,
        max_clients: int = 1000,
    ) -> None:
        self._max_requests = max_requests
        self._window = window_seconds
        self._max_clients = max_clients
        # client_key → list of request timestamps
        self._store: OrderedDict[str, list[float]] = OrderedDict()

    def is_allowed(self, client_key: str) -> bool:
        """Return True if the client is within the rate limit.

        Side effect: records the current request if allowed.
        """
        now = time.monotonic()
        cutoff = now - self._window

        # Evict old entry if needed (LRU)
        if client_key not in self._store and len(self._store) >= self._max_clients:
            self._store.popitem(last=False)

        timestamps = self._store.get(client_key, [])
        # Remove timestamps outside the window
        timestamps = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= self._max_requests:
            return False

        timestamps.append(now)
        self._store[client_key] = timestamps
        self._store.move_to_end(client_key)
        return True

    def reset(self, client_key: str) -> None:
        """Reset the rate limit counter for a client (for testing)."""
        self._store.pop(client_key, None)
