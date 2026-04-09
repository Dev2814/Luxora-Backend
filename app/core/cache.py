import json
from typing import Any, Optional
from app.infrastructure.redis.client import redis_client
from app.core.logger import log_event


# --------------------------------------------------
# SET CACHE
# --------------------------------------------------

def set_cache(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Store data in Redis cache.
    """

    try:

        redis_client.setex(
            key,
            ttl,
            json.dumps(value)
        )

        return True

    except Exception as e:

        log_event(
            "cache_set_error",
            level="error",
            key=key,
            error=str(e)
        )

        return False


# --------------------------------------------------
# GET CACHE
# --------------------------------------------------

def get_cache(key: str) -> Optional[Any]:
    """
    Retrieve cached value.
    """

    try:

        value = redis_client.get(key)

        if not value:
            return None

        return json.loads(value)

    except Exception as e:

        log_event(
            "cache_get_error",
            level="error",
            key=key,
            error=str(e)
        )

        return None


# --------------------------------------------------
# DELETE CACHE
# --------------------------------------------------

def delete_cache(key: str) -> bool:
    """
    Remove cache entry.
    """

    try:

        redis_client.delete(key)
        return True

    except Exception as e:

        log_event(
            "cache_delete_error",
            level="error",
            key=key,
            error=str(e)
        )

        return False


# --------------------------------------------------
# CACHE EXISTS
# --------------------------------------------------

def cache_exists(key: str) -> bool:
    """
    Check if cache key exists.
    """

    try:

        return redis_client.exists(key) == 1

    except Exception as e:

        log_event(
            "cache_exists_error",
            level="error",
            key=key,
            error=str(e)
        )

        return False


# --------------------------------------------------
# CLEAR CACHE PREFIX
# --------------------------------------------------

def clear_cache_prefix(prefix: str):
    """
    Clear all cache keys with a prefix.
    """

    try:

        keys = redis_client.keys(f"{prefix}*")

        if keys:
            redis_client.delete(*keys)

        log_event(
            "cache_prefix_cleared",
            prefix=prefix,
            count=len(keys)
        )

    except Exception as e:

        log_event(
            "cache_clear_prefix_error",
            level="error",
            prefix=prefix,
            error=str(e)
        )