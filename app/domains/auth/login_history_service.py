"""
Login History Service

Handles login activity tracking and suspicious login detection.

Enterprise Features:
- Login attempt recording
- Suspicious IP detection
- Login history retrieval
- Failure tracking
- Security monitoring
"""

from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.login_history import LoginHistory
from app.core.logger import log_event


class LoginHistoryService:

    def __init__(self, db: Session):
        self.db = db

    # =====================================================
    # RECORD LOGIN ATTEMPT
    # =====================================================

    def record_login_attempt(
        self,
        email: str,
        success: bool,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[int] = None,
        failure_reason: Optional[str] = None,
        device_name: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None
    ) -> None:

        try:

            history = LoginHistory(
                user_id=user_id,
                email=email,
                success=success,
                failure_reason=failure_reason,
                ip_address=ip,
                user_agent=user_agent,
                device_name=device_name,
                country=country,
                city=city
            )

            self.db.add(history)
            self.db.commit()

            log_event(
                "login_attempt_recorded",
                email=email,
                success=success,
                ip=ip
            )

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "login_history_error",
                level="critical",
                email=email,
                error=str(e)
            )

    # =====================================================
    # GET USER LOGIN HISTORY
    # =====================================================

    def get_user_login_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[LoginHistory]:

        try:

            return (
                self.db.query(LoginHistory)
                .filter(LoginHistory.user_id == user_id)
                .order_by(LoginHistory.created_at.desc())
                .limit(limit)
                .all()
            )

        except Exception as e:

            log_event(
                "login_history_fetch_error",
                level="critical",
                user_id=user_id,
                error=str(e)
            )

            return []

    # =====================================================
    # DETECT SUSPICIOUS LOGIN
    # =====================================================

    def detect_suspicious_login(
        self,
        user_id: int,
        ip: str
    ) -> bool:

        """
        Detect login from new IP address.
        """

        try:

            last_login = (
                self.db.query(LoginHistory)
                .filter(
                    LoginHistory.user_id == user_id,
                    LoginHistory.success == True
                )
                .order_by(LoginHistory.created_at.desc())
                .first()
            )

            if not last_login:
                return False

            if last_login.ip_address != ip:

                log_event(
                    "suspicious_login_detected",
                    level="warning",
                    user_id=user_id,
                    old_ip=last_login.ip_address,
                    new_ip=ip
                )

                return True

            return False

        except Exception as e:

            log_event(
                "suspicious_login_detection_error",
                level="critical",
                user_id=user_id,
                error=str(e)
            )

            return False

    # =====================================================
    # COUNT FAILED ATTEMPTS
    # =====================================================

    def count_recent_failed_attempts(
        self,
        email: str,
        limit: int = 10
    ) -> int:

        """
        Used for brute force detection.
        """

        try:

            return (
                self.db.query(LoginHistory)
                .filter(
                    LoginHistory.email == email,
                    LoginHistory.success == False
                )
                .order_by(LoginHistory.created_at.desc())
                .limit(limit)
                .count()
            )

        except Exception as e:

            log_event(
                "login_failure_count_error",
                level="critical",
                email=email,
                error=str(e)
            )

            return 0