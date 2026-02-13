"""
Job Cancellation Service Module

Manages cancellation flags in Redis for cooperative job cancellation.
Workers check these flags between lifecycle hooks to detect cancellation
requests and shut down gracefully.
"""

import redis

CANCEL_KEY_PREFIX = "job:cancel:"
CANCEL_TTL = 86400  # 24 hours


class CancellationService:
    """Manages Redis-based cancellation flags for jobs."""

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    def request_cancel(self, job_id: str) -> None:
        """Set a cancellation flag for the given job."""
        self._redis.set(f"{CANCEL_KEY_PREFIX}{job_id}", "1", ex=CANCEL_TTL)

    def is_cancelled(self, job_id: str) -> bool:
        """Check if a cancellation has been requested for the given job."""
        return self._redis.exists(f"{CANCEL_KEY_PREFIX}{job_id}") > 0

    def clear(self, job_id: str) -> None:
        """Remove the cancellation flag for the given job."""
        self._redis.delete(f"{CANCEL_KEY_PREFIX}{job_id}")
