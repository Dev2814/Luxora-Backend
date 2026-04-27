"""
Notification Cleanup Job

Deletes old read notifications after a certain time.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.core.logger import log_event


def delete_old_notifications(db: Session, minutes: int = 1):
    """
    Delete notifications that are:
    - Already read
    - Older than X minutes
    """

    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

    deleted_count = (
        db.query(Notification)
        .filter(
            Notification.is_read == True,
            Notification.read_at != None,
            Notification.read_at <= cutoff_time
        )
        .delete()
    )

    db.commit()

    log_event(
        "notifications_cleanup",
        deleted=deleted_count,
        minutes=minutes
    )