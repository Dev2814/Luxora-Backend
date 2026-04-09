"""
Enterprise Rate Limiter

Provides distributed rate limiting using Redis.

Features:
- Redis-based distributed limiting
- FastAPI dependency integration
- Request counting with expiration window
- Remaining request tracking
- Load-balancer aware IP detection
"""

from fastapi import Request, HTTPException, status
from typing import Tuple
import time

from app.infrastructure.redis.client import redis_client
from app.core.logger import log_event
from app.core.config import settings


# ======================================================
# RATE LIMITER CLASS
# ======================================================

class RateLimiter:
    """
    Redis-based rate limiter.
    """

    def __init__(self, key_prefix: str, limit: int, window_seconds: int):
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window_seconds

    # --------------------------------------------------
    # INTERNAL REDIS KEY
    # --------------------------------------------------

    def _key(self, identifier: str) -> str:
        return f"rate_limit:{self.key_prefix}:{identifier}"

    # --------------------------------------------------
    # CHECK LIMIT
    # --------------------------------------------------

    def check(self, identifier: str) -> Tuple[bool, int, int]:
        """
        Returns:
        (allowed, remaining_requests, reset_timestamp)
        """

        key = self._key(identifier)

        try:

            pipe = redis_client.pipeline()

            pipe.incr(key)
            pipe.ttl(key)

            count, ttl = pipe.execute()

            if count == 1:
                redis_client.expire(key, self.window)
                ttl = self.window

            remaining = max(self.limit - count, 0)

            reset_time = int(time.time()) + (ttl if ttl > 0 else self.window)

            if count > self.limit:

                log_event(
                    "rate_limit_exceeded",
                    level="warning",
                    key=key,
                    identifier=identifier,
                    count=count,
                    limit=self.limit
                )

                return False, remaining, reset_time

            return True, remaining, reset_time

        except Exception as e:

            log_event(
                "rate_limiter_error",
                level="critical",
                key=key,
                identifier=identifier,
                error=str(e)
            )

            # Fail-safe → allow request
            return True, self.limit, int(time.time()) + self.window


# ======================================================
# CLIENT IDENTIFIER
# ======================================================

def get_client_identifier(request: Request) -> str:
    """
    Extract client IP safely, supporting proxies.
    """

    # Cloudflare / proxies
    forwarded = request.headers.get("x-forwarded-for")

    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")

    if real_ip:
        return real_ip

    client = request.client

    return client.host if client else "unknown"


# ======================================================
# DEPENDENCY FACTORY
# ======================================================

def rate_limit_dependency(limiter: RateLimiter):

    async def dependency(request: Request):

        identifier = get_client_identifier(request)

        allowed, remaining, reset = limiter.check(identifier)

        # Attach headers for API clients
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = reset

        if not allowed:

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

    return dependency


# ======================================================
# LIMITER INSTANCES
# ======================================================

login_limiter = RateLimiter(
    key_prefix="login",
    limit=settings.LOGIN_RATE_LIMIT,
    window_seconds=60
)

otp_verify_limiter = RateLimiter(
    key_prefix="verify_otp",
    limit=5,
    window_seconds=60
)

otp_resend_limiter = RateLimiter(
    key_prefix="resend_otp",
    limit=5,
    window_seconds=300
)

api_limiter = RateLimiter(
    key_prefix="api",
    limit=settings.API_RATE_LIMIT,
    window_seconds=60
)


# ======================================================
# FASTAPI DEPENDENCIES
# ======================================================

login_rate_limiter = rate_limit_dependency(login_limiter)

otp_verify_rate_limiter = rate_limit_dependency(otp_verify_limiter)

otp_resend_rate_limiter = rate_limit_dependency(otp_resend_limiter)

api_rate_limiter = rate_limit_dependency(api_limiter)