"""Sliding-window rate limiter with Redis or in-memory backend."""
from __future__ import annotations

import abc
import asyncio
import os
import time
from typing import Any


class RateLimiter(abc.ABC):
    """Abstract rate limiter."""

    @abc.abstractmethod
    async def is_allowed(self, key: str, window_seconds: int, max_requests: int) -> bool: ...


class MemoryRateLimiter(RateLimiter):
    """In-memory sliding-window rate limiter."""

    def __init__(self):
        self._windows: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, window_seconds: int, max_requests: int) -> bool:
        now = time.time()
        async with self._lock:
            window = self._windows.get(key, [])
            # Prune expired entries
            cutoff = now - window_seconds
            window = [t for t in window if t > cutoff]
            if len(window) >= max_requests:
                self._windows[key] = window
                return False
            window.append(now)
            self._windows[key] = window
            return True


class RedisRateLimiter(RateLimiter):
    """Redis-backed sliding-window rate limiter."""

    def __init__(self, redis_url: str):
        import redis.asyncio as redis
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._prefix = "mesh:rl"

    async def is_allowed(self, key: str, window_seconds: int, max_requests: int) -> bool:
        rkey = f"{self._prefix}:{key}"
        now = time.time()
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(rkey, 0, now - window_seconds)
        pipe.zcard(rkey)
        pipe.zadd(rkey, {str(now): now})
        pipe.expire(rkey, window_seconds + 1)
        _, count, _, _ = await pipe.execute()
        if count >= max_requests:
            # Rollback the added timestamp
            await self._redis.zrem(rkey, str(now))
            return False
        return True


def create_rate_limiter() -> RateLimiter:
    redis_url = os.getenv("MESH_REDIS_URL")
    if redis_url:
        return RedisRateLimiter(redis_url)
    return MemoryRateLimiter()
