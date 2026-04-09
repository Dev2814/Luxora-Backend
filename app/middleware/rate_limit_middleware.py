"""
Rate Limit Middleware

Provides global API protection against request flooding.

Architecture:
Client → Middleware → Redis RateLimiter → Route
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.rate_limiter import (
    login_limiter,
    otp_verify_limiter,
    otp_resend_limiter,
    api_limiter,
)
from app.core.logger import log_event


class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:

        try:

            path = request.url.path

            # --------------------------------------------------
            # EXTRACT CLIENT IP (proxy safe)
            # --------------------------------------------------

            forwarded = request.headers.get("x-forwarded-for")

            if forwarded:
                ip = forwarded.split(",")[0].strip()
            else:
                client = request.client
                ip = client.host if client else "unknown"

            # --------------------------------------------------
            # SKIP DOCS
            # --------------------------------------------------

            if path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
                return await call_next(request)

            # --------------------------------------------------
            # SELECT LIMITER
            # --------------------------------------------------

            limiter = self._select_limiter(path)

            # --------------------------------------------------
            # RATE LIMIT CHECK
            # --------------------------------------------------

            allowed, remaining, reset = limiter.check(ip)

            if not allowed:

                log_event(
                    "rate_limit_blocked",
                    level="warning",
                    ip=ip,
                    path=path,
                )

                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please try again later."
                    },
                )

            # --------------------------------------------------
            # PROCESS REQUEST
            # --------------------------------------------------

            response: Response = await call_next(request)

            # --------------------------------------------------
            # RATE LIMIT HEADERS
            # --------------------------------------------------

            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset)

            return response

        except Exception as e:

            log_event(
                "rate_limit_middleware_error",
                level="critical",
                error=str(e),
            )

            # fail-safe
            return await call_next(request)

    # --------------------------------------------------
    # LIMITER ROUTING
    # --------------------------------------------------

    def _select_limiter(self, path: str):

        if path.endswith("/auth/login"):
            return login_limiter

        if path.endswith("/auth/verify-otp"):
            return otp_verify_limiter

        if path.endswith("/auth/resend-otp"):
            return otp_resend_limiter

        return api_limiter