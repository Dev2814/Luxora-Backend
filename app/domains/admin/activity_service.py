"""
Admin Activity Service

Responsible for recording and retrieving admin audit logs.

Purpose:
- Security auditing
- Administrative accountability
- Incident investigation
- Compliance tracking

Architecture:
Service → ActivityService → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, List

from app.models.admin_activity_log import AdminActivityLog
from app.core.logger import log_event


class AdminActivityService:

    def __init__(self, db: Session):
        self.db = db

    # ==================================================
    # LOG ADMIN ACTION
    # ==================================================

    def log_activity(
        self,
        admin_id: Optional[int],
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "INFO"
    ) -> None:
        """
        Store admin action in audit log.

        Example actions:
        - vendor_approved
        - vendor_rejected
        - brand_created
        - user_deactivated
        """

        try:

            if not action:
                raise ValueError("Action cannot be empty")

            activity = AdminActivityLog(
                admin_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                extra_data=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity
            )

            self.db.add(activity)
            self.db.commit()

        except SQLAlchemyError as e:

            self.db.rollback()

            # Logging failure should never break main business logic
            log_event(
                "admin_activity_log_failed",
                level="critical",
                admin_id=admin_id,
                action=action,
                error=str(e)
            )

        except ValueError as e:

            log_event(
                "admin_activity_invalid_action",
                level="warning",
                action=action,
                error=str(e)
            )

    # ==================================================
    # GET ADMIN ACTIVITY HISTORY
    # ==================================================

    def get_admin_activity(
        self,
        admin_id: int,
        limit: int = 100
    ) -> List[AdminActivityLog]:
        """
        Fetch recent activity for a specific admin.
        """

        try:

            logs = (
                self.db.query(AdminActivityLog)
                .filter(AdminActivityLog.admin_id == admin_id)
                .order_by(AdminActivityLog.created_at.desc())
                .limit(limit)
                .all()
            )

            return logs

        except Exception as e:

            log_event(
                "admin_activity_fetch_error",
                level="critical",
                admin_id=admin_id,
                error=str(e)
            )

            return []

    # ==================================================
    # GET GLOBAL ACTIVITY
    # ==================================================

    def get_recent_activity(
        self,
        limit: int = 50
    ) -> List[AdminActivityLog]:
        """
        Fetch latest admin activity across platform.
        Useful for admin dashboard.
        """

        try:

            logs = (
                self.db.query(AdminActivityLog)
                .order_by(AdminActivityLog.created_at.desc())
                .limit(limit)
                .all()
            )

            return logs

        except Exception as e:

            log_event(
                "admin_global_activity_fetch_error",
                level="critical",
                error=str(e)
            )

            return []

    # ==================================================
    # SEARCH ACTIVITY
    # ==================================================

    def search_activity(
        self,
        action: Optional[str] = None,
        admin_id: Optional[int] = None,
        limit: int = 100
    ) -> List[AdminActivityLog]:
        """
        Search activity logs with filters.
        """

        try:

            query = self.db.query(AdminActivityLog)

            if action:
                query = query.filter(AdminActivityLog.action == action)

            if admin_id:
                query = query.filter(AdminActivityLog.admin_id == admin_id)

            logs = (
                query.order_by(AdminActivityLog.created_at.desc())
                .limit(limit)
                .all()
            )

            return logs

        except Exception as e:

            log_event(
                "admin_activity_search_error",
                level="critical",
                error=str(e)
            )

            return []