"""
Enterprise Security Headers Middleware

Adds security headers to all responses to protect against:
- Clickjacking
- MIME sniffing
- XSS attacks
- Data leakage
- Mixed content attacks

Also adds request tracing.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import Response

from app.core.logger import log_event
from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # --------------------------------------------------
        # REQUEST ID
        # --------------------------------------------------

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        try:
            response: Response = await call_next(request)

        except Exception as e:

            log_event(
                "middleware_request_error",
                level="critical",
                path=request.url.path,
                error=str(e),
            )

            raise

        # --------------------------------------------------
        # SECURITY HEADERS
        # --------------------------------------------------

        headers = response.headers

        # Prevent clickjacking
        headers["X-Frame-Options"] = "DENY"

        # Prevent MIME sniffing
        headers["X-Content-Type-Options"] = "nosniff"

        # Basic XSS protection
        headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer protection
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disable browser features
        headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        # Prevent caching
        headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

        # Remove server fingerprint
        if "server" in headers:
            del headers["server"]

        # Add request ID to response
        headers["X-Request-ID"] = request_id

        # --------------------------------------------------
        # HSTS (only production)
        # --------------------------------------------------

        if settings.ENVIRONMENT == "production":
            headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # --------------------------------------------------
        # CONTENT SECURITY POLICY
        # --------------------------------------------------

        path = request.url.path

        # Relax CSP for documentation
        if path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):

            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;"
            )

        else:

            headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "frame-ancestors 'none'; "
                "img-src 'self' data:; "
                "script-src 'self'; "
                "style-src 'self'; "
                "connect-src 'self';"
            )

        # --------------------------------------------------
        # LOG REQUEST
        # --------------------------------------------------

        log_event(
            "api_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )

        return response