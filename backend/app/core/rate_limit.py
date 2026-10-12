import time
from collections import defaultdict
from threading import Lock

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import AppError


class FixedWindowLimiter:
    """In-process limiter for a single API instance. Swap for Redis when scaling out."""

    def __init__(self) -> None:
        self._hits: dict[tuple[str, str, int], int] = defaultdict(int)
        self._lock = Lock()

    def hit(self, scope: str, key: str, limit: int) -> bool:
        window = int(time.time() // 60)
        with self._lock:
            if len(self._hits) > 10_000:
                self._hits = defaultdict(
                    int, {k: v for k, v in self._hits.items() if k[2] == window}
                )
            self._hits[(scope, key, window)] += 1
            return self._hits[(scope, key, window)] <= limit

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = FixedWindowLimiter()


def rate_limited(scope: str):
    def dependency(request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        if not limiter.hit(scope, key, get_settings().rate_limit_per_minute):
            raise AppError(429, "rate_limited", "Too many requests. Try again in a minute.")

    return dependency
