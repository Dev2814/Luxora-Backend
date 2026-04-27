"""
Notification Repository

Handles all database operations related to notifications.

Responsibilities:
- Create notification records
- Fetch notifications for a user
- Update read status
- Bulk operations

Architecture:
Service → Repository → Database
"""

from sqlalchemy.orm import Session
from typing import List

from app.models.notification import Notification


class NotificationRepository:
    """
    Repository layer for notification persistence.
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================
    # CREATE NOTIFICATION
    # =========================================================
    def create_notification(self, notification: Notification) -> Notification:
        """
        Save a new notification to the database.
        """
        self.db.add(notification)
        self.db.flush()  # get ID before commit
        return notification

    # =========================================================
    # GET USER NOTIFICATIONS
    # =========================================================
    def get_user_notifications(self, user_id: int) -> List[Notification]:
        """
        Fetch all notifications for a user (latest first).
        """
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

    # =========================================================
    # MARK SINGLE AS READ
    # =========================================================
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        Mark a specific notification as read.
        """
        notification = (
            self.db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
            .first()
        )

        if not notification:
            return False

        notification.is_read = True
        return True

    # =========================================================
    # MARK ALL AS READ
    # =========================================================
    def mark_all_as_read(self, user_id: int) -> int:
        """
        Mark all notifications as read for a user.
        Returns number of updated rows.
        """
        updated = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .update({"is_read": True})
        )

        return updated