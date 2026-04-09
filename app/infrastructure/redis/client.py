"""
Redis Client

Provides:
- Redis connection management
- Cache helpers
- Safe Redis operations
- Enterprise connection pooling
"""

import redis
from redis.exceptions import RedisError, ConnectionError

from app.core.config import settings
from app.core.logger import log_event


# ==========================================================
# REDIS CONNECTION
# ==========================================================

def create_redis_client():

    try:

        client = redis.Redis.from_url(
            str(settings.REDIS_URL),  # convert AnyUrl → string

            decode_responses=True,

            # -----------------------------
            # CONNECTION POOL
            # -----------------------------
            max_connections=100,

            # -----------------------------
            # TIMEOUTS
            # -----------------------------
            socket_timeout=5,
            socket_connect_timeout=5,

            # -----------------------------
            # HEALTH CHECK
            # -----------------------------
            health_check_interval=30,

            retry_on_timeout=True
        )

        # Test connection
        client.ping()

        log_event("redis_connected")

        return client

    except Exception as e:

        log_event(
            "redis_connection_failed",
            level="critical",
            error=str(e)
        )

        # Return None instead of crashing app
        return None


redis_client = create_redis_client()


# ==========================================================
# CACHE HELPERS
# ==========================================================

def set_cache(key: str, value: str, ttl: int = 300):
    """
    Set value in Redis cache.
    """

    if not redis_client:
        return

    try:

        redis_client.setex(key, ttl, value)

    except RedisError as e:

        log_event(
            "redis_set_cache_error",
            level="warning",
            key=key,
            error=str(e)
        )


def get_cache(key: str):
    """
    Retrieve value from Redis cache.
    """

    if not redis_client:
        return None

    try:

        return redis_client.get(key)

    except RedisError as e:

        log_event(
            "redis_get_cache_error",
            level="warning",
            key=key,
            error=str(e)
        )

        return None


def delete_cache(key: str):
    """
    Delete cache key.
    """

    if not redis_client:
        return

    try:

        redis_client.delete(key)

    except RedisError as e:

        log_event(
            "redis_delete_cache_error",
            level="warning",
            key=key,
            error=str(e)
        )