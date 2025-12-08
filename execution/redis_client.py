"""
Redis client and utilities for caching, locking, and deduplication
"""
import redis
from contextlib import contextmanager
from typing import Optional
from loguru import logger
from execution.config import get_redis_url, settings


class RedisClient:
    """Redis client wrapper"""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or get_redis_url()
        self._client = None

    def connect(self):
        """Establish Redis connection"""
        if not self._client:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=True
                )
                self._client.ping()
                logger.info("Redis connected successfully")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                raise
        return self._client

    def get_client(self):
        """Get Redis client"""
        return self.connect()

    @contextmanager
    def lock(self, key: str, timeout: Optional[int] = None):
        """
        Distributed lock context manager

        Usage:
            with redis_client.lock("conversation:123"):
                # Do work
                pass
        """
        client = self.get_client()
        timeout = timeout or settings.redis_lock_timeout
        lock_key = f"lock:{key}"

        lock = client.lock(lock_key, timeout=timeout, blocking_timeout=timeout)

        try:
            acquired = lock.acquire(blocking=True)
            if not acquired:
                raise TimeoutError(f"Could not acquire lock for {key}")
            logger.debug(f"Lock acquired: {key}")
            yield lock
        finally:
            try:
                lock.release()
                logger.debug(f"Lock released: {key}")
            except redis.exceptions.LockError:
                logger.warning(f"Lock already released: {key}")

    def set_with_ttl(self, key: str, value: str, ttl: int):
        """Set key with TTL (time to live in seconds)"""
        client = self.get_client()
        client.setex(key, ttl, value)

    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        client = self.get_client()
        return client.get(key)

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        client = self.get_client()
        return client.exists(key) > 0

    def delete(self, key: str):
        """Delete key"""
        client = self.get_client()
        client.delete(key)

    def increment(self, key: str) -> int:
        """Increment counter"""
        client = self.get_client()
        return client.incr(key)

    def decrement(self, key: str) -> int:
        """Decrement counter"""
        client = self.get_client()
        return client.decr(key)


# Global Redis instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Get Redis client instance"""
    return redis_client
