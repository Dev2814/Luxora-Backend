"""
Redis Cache Service

Provides a clean abstraction over Redis caching.

Features:
- JSON serialization support
- Safe Redis operations
- TTL support
- Structured logging
- Graceful Redis failure handling
"""

import json
from typing import Any, Optional

from redis.exceptions import RedisError

from app.infrastructure.redis.client import redis_client
from app.core.logger import log_event


# ==========================================================
# CACHE SET
# ==========================================================

def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Store value in Redis cache.

    Args:
        key: cache key
        value: any serializable object
        ttl: time to live (seconds)
    """

    if not redis_client:
        return False

    try:

        serialized = json.dumps(value)

        redis_client.setex(key, ttl, serialized)

        return True

    except (RedisError, TypeError) as e:

        log_event(
            "cache_set_failed",
            level="warning",
            key=key,
            error=str(e)
        )

        return False


# ==========================================================
# CACHE GET
# ==========================================================

def cache_get(key: str) -> Optional[Any]:
    """
    Retrieve cached value.
    """

    if not redis_client:
        return None

    try:

        data = redis_client.get(key)

        if not data:
            return None

        return json.loads(data)

    except (RedisError, json.JSONDecodeError) as e:

        log_event(
            "cache_get_failed",
            level="warning",
            key=key,
            error=str(e)
        )

        return None


# ==========================================================
# CACHE DELETE
# ==========================================================

def cache_delete(key: str) -> bool:
    """
    Remove cache key.
    """

    if not redis_client:
        return False

    try:

        redis_client.delete(key)

        return True

    except RedisError as e:

        log_event(
            "cache_delete_failed",
            level="warning",
            key=key,
            error=str(e)
        )

        return False


# ==========================================================
# CACHE EXISTS
# ==========================================================

def cache_exists(key: str) -> bool:
    """
    Check if cache key exists.
    """

    if not redis_client:
        return False

    try:

        return bool(redis_client.exists(key))

    except RedisError as e:

        log_event(
            "cache_exists_failed",
            level="warning",
            key=key,
            error=str(e)
        )

        return False


# ==========================================================
# CACHE CLEAR PATTERN
# ==========================================================

def cache_clear_pattern(pattern: str) -> int:
    """
    Delete keys matching pattern.

    Example:
        cache_clear_pattern("product:*")
    """

    if not redis_client:
        return 0

    deleted = 0

    try:

        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)
            deleted += 1

        return deleted

    except RedisError as e:

        log_event(
            "cache_pattern_delete_failed",
            level="warning",
            pattern=pattern,
            error=str(e)
        )

        return 0