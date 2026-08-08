import asyncio
import time
from collections import defaultdict, deque

from app.common.constants import ErrorCode
from app.common.exceptions import AppError


class SlidingWindowRateLimiter:
    """Small in-memory limiter for the Week-5 single-instance demo; replace with Redis when scaling."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> None:
        """Allow a request or raise 429 when the configured sliding-window budget is exhausted."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        async with self._lock:
            events = self._events[key]
            while events and events[0] < cutoff:
                events.popleft()
            if len(events) >= self._max_requests:
                raise AppError(ErrorCode.RATE_LIMITED, "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.", 429)
            events.append(now)
