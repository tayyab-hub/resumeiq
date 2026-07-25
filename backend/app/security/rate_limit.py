"""In-process fixed-window rate limiting.

Known limitation, stated in the README: counters live in the worker's memory,
so limits are per-process. A multi-instance deployment would move this to Redis.
For a single-instance deployment it is accurate, and it has no infrastructure
cost.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _prune(self, key: str, window_seconds: int, now: float) -> list[float]:
        cutoff = now - window_seconds
        kept = [ts for ts in self._hits[key] if ts > cutoff]
        self._hits[key] = kept
        return kept

    def check(self, key: str, limit: int, window_seconds: int) -> int | None:
        """Return None if allowed, or the number of seconds to wait if blocked.

        Does not record the attempt; call `hit` for that.
        """
        now = time.monotonic()
        with self._lock:
            kept = self._prune(key, window_seconds, now)
            if len(kept) < limit:
                return None
            retry_after = int(window_seconds - (now - kept[0])) + 1
            return max(retry_after, 1)

    def hit(self, key: str, window_seconds: int) -> None:
        now = time.monotonic()
        with self._lock:
            self._prune(key, window_seconds, now)
            self._hits[key].append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


# One shared instance. Separate key namespaces keep the concerns apart.
limiter = RateLimiter()

SECONDS_PER_DAY = 86_400
SECONDS_PER_HOUR = 3_600
