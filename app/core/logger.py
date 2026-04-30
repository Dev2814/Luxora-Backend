# """
# Application Logger

# Centralized structured logging for the Luxora backend.

# Features:
# - Structured JSON logging
# - Standard severity levels
# - Automatic timestamps (UTC)
# - Critical error alert emails
# - Fail-safe logging (never crashes the application)

# Architecture:
# Application → log_event() → Python Logger → Log File / Console
# """

# import logging
# import json
# from datetime import datetime, timezone
# from typing import Any, Dict, Optional

# from app.infrastructure.email.service import send_email
# from app.core.config import settings


# # ==================================================
# # LOGGER INSTANCE
# # ==================================================

# logger = logging.getLogger("luxora")


# # ==================================================
# # MAIN STRUCTURED LOG FUNCTION
# # ==================================================

# def log_event(
#     event: str,
#     level: str = "info",
#     request_id: Optional[str] = None,
#     **kwargs: Any
# ) -> None:
#     """
#     Central logging function used across the application.

#     Example:
#         log_event(
#             "user_login",
#             user_id=12,
#             ip="127.0.0.1"
#         )
#     """

#     try:

#         log_data: Dict[str, Any] = {
#             "event": event,
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#         }

#         # Attach request tracing ID if available
#         if request_id:
#             log_data["request_id"] = request_id

#         # Add additional structured fields
#         log_data.update(kwargs)

#         message = json.dumps(log_data, default=str)

#         level = level.lower()

#         if level == "info":
#             logger.info(message)

#         elif level == "warning":
#             logger.warning(message)

#         elif level == "error":
#             logger.error(message)

#         elif level == "critical":
#             logger.critical(message)
#             send_error_alert(message)

#         else:
#             logger.info(message)

#     except Exception as logging_error:

#         # Last-resort fallback logging
#         try:
#             logger.error(
#                 json.dumps({
#                     "event": "logging_failure",
#                     "timestamp": datetime.now(timezone.utc).isoformat(),
#                     "error": str(logging_error)
#                 })
#             )
#         except Exception:
#             pass


# # ==================================================
# # CRITICAL ERROR ALERT EMAIL
# # ==================================================

# def send_error_alert(message: str) -> None:
#     """
#     Send email alert for critical backend errors.
#     Used for production monitoring.
#     """

#     try:

#         admin_email = settings.ADMIN_ALERT_EMAIL

#         if not admin_email:
#             logger.warning(
#                 json.dumps({
#                     "event": "admin_alert_email_not_configured",
#                     "timestamp": datetime.now(timezone.utc).isoformat()
#                 })
#             )
#             return

#         send_email(
#             to_email=admin_email,
#             subject="Luxora Critical Backend Error",
#             template_name="error_alert.html",
#             context={
#                 "message": message,
#                 "year": datetime.now(timezone.utc).year,
#                 "title": "Critical System Error"
#             }
#         )

#     except Exception as email_error:

#         logger.error(
#             json.dumps({
#                 "event": "error_alert_email_failure",
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "error": str(email_error)
#             })
#         )





"""
Application Logger (Enterprise Grade)

Enhancements:
- Environment-aware logging
- Async-safe critical alerts
- Structured exception logging
- Auto request_id generation
- Log schema standardization
- Performance metadata
- Alert throttling (basic)
"""

import logging
import json
import socket
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from app.infrastructure.email.service import send_email
from app.core.config import settings


# ==================================================
# LOGGER INSTANCE
# ==================================================

logger = logging.getLogger("luxora")


# ==================================================
# INTERNAL CONFIG
# ==================================================

SERVICE_NAME = "luxora-backend"
HOSTNAME = socket.gethostname()

# Simple in-memory throttle (can move to Redis later)
LAST_ALERT_TIME = None
ALERT_COOLDOWN_SECONDS = 60


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
    Central structured logger.

    Guarantees:
    - Never crashes application
    - Always logs valid JSON
    """

    try:
        # --------------------------------------------------
        # ENSURE REQUEST ID (TRACEABILITY)
        # --------------------------------------------------
        if not request_id:
            request_id = str(uuid4())

        # --------------------------------------------------
        # BASE LOG STRUCTURE
        # --------------------------------------------------
        log_data: Dict[str, Any] = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "service": SERVICE_NAME,
            "environment": settings.ENVIRONMENT,
            "host": HOSTNAME,
        }

        # --------------------------------------------------
        # STRUCTURED EXCEPTION HANDLING
        # --------------------------------------------------
        if "error" in kwargs and isinstance(kwargs["error"], Exception):
            exc = kwargs.pop("error")

            log_data.update({
                "error_message": str(exc),
                "error_type": type(exc).__name__,
                "stack_trace": traceback.format_exc()
            })

        # --------------------------------------------------
        # ATTACH EXTRA FIELDS
        # --------------------------------------------------
        log_data.update(kwargs)

        message = json.dumps(log_data, default=str)

        level = level.lower()

        # --------------------------------------------------
        # LOG DISPATCH
        # --------------------------------------------------
        if level == "info":
            logger.info(message)

        elif level == "warning":
            logger.warning(message)

        elif level == "error":
            logger.error(message)

        elif level == "critical":
            logger.critical(message)
            send_error_alert_async(message)

        else:
            logger.info(message)

    except Exception as logging_error:
        # --------------------------------------------------
        # FAIL-SAFE LOGGER
        # --------------------------------------------------
        try:
            logger.error(json.dumps({
                "event": "logging_failure",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(logging_error)
            }))
        except Exception:
            pass


# ==================================================
# ASYNC SAFE ALERT TRIGGER
# ==================================================

def send_error_alert_async(message: str) -> None:
    """
    Prevent blocking main thread.
    """

    import threading

    thread = threading.Thread(
        target=send_error_alert,
        args=(message,),
        daemon=True
    )
    thread.start()


# ==================================================
# CRITICAL ERROR ALERT EMAIL
# ==================================================

def send_error_alert(message: str) -> None:
    """
    Sends alert email (Production only + throttled)
    """

    global LAST_ALERT_TIME

    try:
        # --------------------------------------------------
        # ENVIRONMENT CHECK
        # --------------------------------------------------
        if settings.ENVIRONMENT != "production":
            return

        # --------------------------------------------------
        # THROTTLING (BASIC)
        # --------------------------------------------------
        now = datetime.now(timezone.utc)

        if LAST_ALERT_TIME:
            diff = (now - LAST_ALERT_TIME).total_seconds()
            if diff < ALERT_COOLDOWN_SECONDS:
                return

        LAST_ALERT_TIME = now

        # --------------------------------------------------
        # EMAIL CONFIG
        # --------------------------------------------------
        admin_email = settings.ADMIN_ALERT_EMAIL

        if not admin_email:
            logger.warning(json.dumps({
                "event": "admin_alert_email_not_configured",
                "timestamp": now.isoformat()
            }))
            return

        # --------------------------------------------------
        # SEND EMAIL
        # --------------------------------------------------
        send_email(
            to_email=admin_email,
            subject="🚨 Luxora Critical Backend Error",
            template_name="error_alert.html",
            context={
                "message": message,
                "year": now.year,
                "title": "Critical System Error"
            }
        )

    except Exception as email_error:
        logger.error(json.dumps({
            "event": "error_alert_email_failure",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(email_error)
        }))