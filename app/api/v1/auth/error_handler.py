"""
Authentication Exception Handler

Handles unexpected authentication system failures.
Logs the error and optionally notifies administrators.

Enterprise Features:
- Structured logging
- Proxy-safe IP detection
- Request tracing support
- Production-only alerting
- Safe error responses
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logger import log_event
from app.infrastructure.email.service import send_email
from app.core.config import settings


# ==========================================================
# CLIENT IP DETECTION
# ==========================================================

def get_client_ip(request: Request) -> str:
    """
    Extract client IP safely (supports proxies / load balancers).
    """

    forwarded = request.headers.get("x-forwarded-for")

    if forwarded:
        return forwarded.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


# ==========================================================
# AUTH EXCEPTION HANDLER
# ==========================================================

async def auth_exception_handler(request: Request, exc: Exception):
    """
    Global handler for unexpected authentication errors.
    """

    try:

        path = request.url.path
        method = request.method
        ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # request tracing from middleware
        request_id = getattr(request.state, "request_id", None)

        # --------------------------------------------------
        # LOG CRITICAL ERROR
        # --------------------------------------------------

        log_event(
            event="auth_system_crash",
            level="critical",
            path=path,
            method=method,
            ip=ip,
            user_agent=user_agent,
            request_id=request_id,
            error=str(exc)
        )

        # --------------------------------------------------
        # SEND ADMIN ALERT (PRODUCTION ONLY)
        # --------------------------------------------------

        if settings.ENVIRONMENT.lower() == "production" and settings.ADMIN_ALERT_EMAIL:

            try:

                send_email(
                    to_email=settings.ADMIN_ALERT_EMAIL,
                    subject="🚨 Luxora Authentication System Error",
                    template_name="error_alert.html",
                    context={
                        "title": "Authentication System Error",
                        "path": path,
                        "method": method,
                        "ip": ip,
                        "user_agent": user_agent,
                        "request_id": request_id,
                        "error": str(exc)
                    }
                )

            except Exception as email_error:

                log_event(
                    "auth_error_email_failed",
                    level="error",
                    error=str(email_error)
                )

    except Exception as handler_error:

        # Prevent recursive crash in handler
        log_event(
            "auth_exception_handler_failure",
            level="critical",
            error=str(handler_error)
        )

    # --------------------------------------------------
    # SAFE CLIENT RESPONSE
    # --------------------------------------------------

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "AUTH_SERVICE_ERROR",
                "message": "Authentication service temporarily unavailable"
            }
        }
    )