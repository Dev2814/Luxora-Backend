"""
Firebase Cloud Messaging (FCM) Service
=======================================

Sends push notifications to vendor Android devices via Firebase.

Design Principles:
------------------
• Lazy-initialize Firebase app (only once per process)
• Graceful failure — notification errors NEVER crash the order flow
• Returns True on success, False on failure for caller awareness
• Supports data payload for deep-link routing in Flutter

Usage:
------
    from app.infrastructure.firebase.fcm import send_push_notification

    success = send_push_notification(
        fcm_token="device-fcm-token",
        title="New Order Received",
        body="John placed an order for Nike Air (Size 42)",
        data={"order_id": "123", "type": "new_order"}
    )
"""

import os
import json
from typing import Optional

from app.core.logger import log_event
from app.core.config import settings


# =========================================================
# FIREBASE APP (LAZY SINGLETON)
# =========================================================

_firebase_initialized = False

# =========================================================
# APP-SPECIFIC CONFIGURATION
# =========================================================

APP_NOTIFICATION_CONFIG = {
    "customer": {
        "channel_id": "luxora_customer",
    },
    "vendor": {
        "channel_id": "luxora_orders",
    }
}


def _initialize_firebase():
    """
    Initialize Firebase Admin SDK exactly once per process.

    Reads credentials from FIREBASE_CREDENTIALS_PATH env variable.
    Falls back gracefully if credentials are missing.
    """

    global _firebase_initialized

    if _firebase_initialized:
        return True

    try:

        import firebase_admin
        from firebase_admin import credentials

        # -------------------------------------------------
        # LOAD CREDENTIALS
        # -------------------------------------------------
        creds_path = settings.FIREBASE_CREDENTIALS_PATH

        if not os.path.exists(creds_path):
            log_event(
                "firebase_credentials_missing",
                level="warning",
                path=creds_path
            )
            return False

        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)

        _firebase_initialized = True

        log_event("firebase_initialized", level="info")

        return True

    except ImportError:
        log_event(
            "firebase_admin_not_installed",
            level="warning",
            hint="Run: pip install firebase-admin"
        )
        return False

    except Exception as e:
        log_event(
            "firebase_init_error",
            level="error",
            error=str(e)
        )
        return False


# =========================================================
# SEND PUSH NOTIFICATION
# =========================================================

def send_push_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
    app_type: str = "customer"
) -> bool:
    """
    Send a Firebase push notification to a device (vendor/customer).

    Parameters:
    -----------
    fcm_token : str
        The device FCM registration token (vendor or customer)
    title : str
        Notification title shown on Android
    body : str
        Notification body text
    data : dict, optional
        Extra key-value data for Flutter deep-link routing
        Example: {"order_id": "42", "type": "new_order"}

    Returns:
    --------
    bool
        True if sent successfully, False on any failure
    """

    if not fcm_token:
        log_event(
            "fcm_token_missing",
            level="warning",
            hint="User has no FCM token registered"
        )
        return False

    # -------------------------------------------------
    # ENSURE FIREBASE IS READY
    # -------------------------------------------------
    if not _initialize_firebase():
        return False

    try:

        from firebase_admin import messaging

        # -------------------------------------------------
        # APP CONFIG
        # -------------------------------------------------

        config = APP_NOTIFICATION_CONFIG.get(app_type, APP_NOTIFICATION_CONFIG["customer"])

        # -------------------------------------------------
        # BUILD MESSAGE
        # -------------------------------------------------
        message = messaging.Message(
            token=fcm_token,

            notification=messaging.Notification(
                title=title,
                body=body,
            ),

            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    channel_id=config["channel_id"],
                    click_action="FLUTTER_NOTIFICATION_CLICK"
                )
            ),

            # Data payload for Flutter deep-link routing
            data={k: str(v) for k, v in (data or {}).items()}
        )

        # -------------------------------------------------
        # SEND
        # -------------------------------------------------
        response = messaging.send(message)

        log_event(
            "fcm_notification_sent",
            level="info",
            app_type=app_type,
            fcm_response=response
        )

        return True

    except Exception as e:

        log_event(
            "fcm_notification_failed",
            level="error",
            error=str(e),
            fcm_token=fcm_token[:20] + "..."  # truncate for safety
        )

        return False
