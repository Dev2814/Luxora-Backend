"""
Notification Cleanup Job

Deletes old read notifications after a certain time.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings


from app.models.notification import Notification
from app.core.logger import log_event

def delete_old_notifications(db: Session, minutes: int = None):

    from app.core.config import settings

    minutes = settings.NOTIFICATION_DELETE_AFTER_MINUTES

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