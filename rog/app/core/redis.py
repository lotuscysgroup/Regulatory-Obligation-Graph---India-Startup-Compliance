from __future__ import annotations

import redis


_redis_client: redis.Redis | None = None


def init_redis(redis_url: str) -> redis.Redis:
    global _redis_client
    _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def get_redis() -> redis.Redis:
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis().")
    return _redis_client

