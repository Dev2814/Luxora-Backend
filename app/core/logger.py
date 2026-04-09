"""
Application Logger

Centralized structured logging for the Luxora backend.

Features:
- Structured JSON logging
- Standard severity levels
- Automatic timestamps (UTC)
- Critical error alert emails
- Fail-safe logging (never crashes the application)

Architecture:
Application → log_event() → Python Logger → Log File / Console
"""

import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.infrastructure.email.service import send_email
from app.core.config import settings


# ==================================================
# LOGGER INSTANCE
# ==================================================

logger = logging.getLogger("luxora")


# ==================================================
# MAIN STRUCTURED LOG FUNCTION
# ==================================================

def log_event(
    event: str,
    level: str = "info",
    request_id: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Central logging function used across the application.

    Example:
        log_event(
            "user_login",
            user_id=12,
            ip="127.0.0.1"
        )
    """

    try:

        log_data: Dict[str, Any] = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Attach request tracing ID if available
        if request_id:
            log_data["request_id"] = request_id

        # Add additional structured fields
        log_data.update(kwargs)

        message = json.dumps(log_data, default=str)

        level = level.lower()

        if level == "info":
            logger.info(message)

        elif level == "warning":
            logger.warning(message)

        elif level == "error":
            logger.error(message)

        elif level == "critical":
            logger.critical(message)
            send_error_alert(message)

        else:
            logger.info(message)

    except Exception as logging_error:

        # Last-resort fallback logging
        try:
            logger.error(
                json.dumps({
                    "event": "logging_failure",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(logging_error)
                })
            )
        except Exception:
            pass


# ==================================================
# CRITICAL ERROR ALERT EMAIL
# ==================================================

def send_error_alert(message: str) -> None:
    """
    Send email alert for critical backend errors.
    Used for production monitoring.
    """

    try:

        admin_email = settings.ADMIN_ALERT_EMAIL

        if not admin_email:
            logger.warning(
                json.dumps({
                    "event": "admin_alert_email_not_configured",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            )
            return

        send_email(
            to_email=admin_email,
            subject="Luxora Critical Backend Error",
            template_name="error_alert.html",
            context={
                "message": message,
                "year": datetime.now(timezone.utc).year,
                "title": "Critical System Error"
            }
        )

    except Exception as email_error:

        logger.error(
            json.dumps({
                "event": "error_alert_email_failure",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(email_error)
            })
        )