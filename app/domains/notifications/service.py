"""
Notification Service

Central business logic for handling notifications.

Responsibilities:
- Create notifications
- Send Firebase push notifications
- Handle role-based notification logic (vendor/customer)
- Provide reusable notification APIs for all domains

Architecture:
Routes / Services → NotificationService → Repository + FCM
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.models.notification import Notification
from app.domains.notifications.repository import NotificationRepository
from app.infrastructure.firebase.fcm import send_push_notification
from app.core.logger import log_event


class NotificationService:
    """
    Core notification engine for Luxora.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    # =========================================================
    # CREATE + SEND NOTIFICATION
    # =========================================================
    def create_and_send(
        self,
        user_id: int,
        title: str,
        message: str,
        fcm_token: Optional[str] = None,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        app_type: str = "customer"
    ):
        """
        Create a notification and optionally send push notification.

        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification message
            fcm_token: Device token (if available)
            reference_id: Related entity ID (order, payment, etc.)
            reference_type: Type of reference (order, payment, etc.)
            data: Extra payload for frontend
        """

        try:
            # -------------------------------
            # CREATE DB NOTIFICATION
            # -------------------------------
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                reference_id=reference_id,
                reference_type=reference_type
            )

            self.repo.create_notification(notification)

            # -------------------------------
            # SEND PUSH NOTIFICATION
            # -------------------------------
            if fcm_token:
                send_push_notification(
                    fcm_token=fcm_token,
                    title=title,
                    body=message,
                    data=data or {},
                    app_type=app_type 
                )

            self.db.commit()

            log_event(
                "notification_created",
                user_id=user_id,
                reference_id=reference_id,
                reference_type=reference_type
            )

        except Exception as e:
            self.db.rollback()

            log_event(
                "notification_failed",
                level="error",
                user_id=user_id,
                error=str(e)
            )

    # =========================================================
    # FETCH USER NOTIFICATIONS
    # =========================================================
    def get_user_notifications(self, user_id: int):
        """
        Get all notifications for a user.
        """
        return self.repo.get_user_notifications(user_id)

    # =========================================================
    # MARK AS READ
    # =========================================================
    def mark_as_read(self, notification_id: int, user_id: int):
        """
        Mark a notification as read.
        """
        success = self.repo.mark_as_read(notification_id, user_id)

        if success:
            self.db.commit()

        return success

    # =========================================================
    # MARK ALL AS READ
    # =========================================================
    def mark_all_as_read(self, user_id: int):
        """
        Mark all notifications as read.
        """
        updated = self.repo.mark_all_as_read(user_id)
        self.db.commit()
        return updated