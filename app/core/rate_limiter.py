import time
from collections import defaultdict
from threading import Lock
from ..config import settings


class RateLimiter:
    """
    Thread-safe sliding window rate limiter per client IP address.
    """

    def __init__(self):
        self._lock = Lock()
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(
        self,
        client_ip: str,
        limit: int = 10,
        window_seconds: float = 1.0,
    ) -> bool:
        """
        Check if a request from client_ip is within the allowed rate limit.

        Args:
            client_ip: IP address of the incoming client.
            limit: Maximum allowed requests per window.
            window_seconds: Duration of the sliding time window in seconds.

        Returns:
            True if request is permitted, False if limit exceeded.
        """
        if not getattr(settings, "ENABLE_RATE_LIMIT", True) or limit <= 0:
            return True

        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Purge timestamps older than the sliding window
            timestamps = [t for t in self._requests[client_ip] if t > cutoff]

            if len(timestamps) >= limit:
                self._requests[client_ip] = timestamps
                return False

            timestamps.append(now)
            self._requests[client_ip] = timestamps
            return True

    def reset(self):
        """Purge all tracked IP timestamps (used in test isolation)."""
        with self._lock:
            self._requests.clear()


rate_limiter = RateLimiter()
