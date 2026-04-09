"""
Session Service

Handles refresh tokens and login sessions.

Responsibilities:
- Create login session
- Validate refresh token
- Rotate refresh token
- Logout (revoke session)
- Revoke all sessions
- Detect refresh token reuse
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user_sessions import UserSession
from app.core.security import hash_token, create_refresh_token
from app.core.logger import log_event

SESSION_EXPIRY_DAYS = 7
MAX_SESSIONS_PER_USER = 5


class SessionService:

    def __init__(self, db: Session):
        self.db = db

    # =====================================================
    # CREATE SESSION
    # =====================================================

    def create_session(self, user_id: int, ip: str, user_agent: str):

        try:

            refresh_token = create_refresh_token()
            token_hash = hash_token(refresh_token)

            # --------------------------------------------------
            # LIMIT ACTIVE SESSIONS
            # --------------------------------------------------

            sessions = (
                self.db.query(UserSession)
                .filter(
                    UserSession.user_id == user_id,
                    UserSession.is_revoked == False
                )
                .order_by(UserSession.created_at.asc())
                .all()
            )

            if len(sessions) >= MAX_SESSIONS_PER_USER:

                oldest = sessions[0]

                oldest.is_revoked = True
                oldest.revoked_at = datetime.utcnow()

                log_event(
                    "old_session_revoked",
                    user_id=user_id,
                    session_id=oldest.id
                )

            # --------------------------------------------------
            # CREATE SESSION
            # --------------------------------------------------

            now = datetime.utcnow()

            session = UserSession(
                user_id=user_id,
                refresh_token_hash=token_hash,
                ip_address=ip,
                user_agent=user_agent,
                created_at=now,
                last_used_at=now,
                expires_at=now + timedelta(days=SESSION_EXPIRY_DAYS),
                is_active=True,
                is_revoked=False
            )

            self.db.add(session)
            self.db.commit()

            log_event(
                "session_created",
                user_id=user_id,
                ip=ip
            )

            return refresh_token

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "session_creation_failed",
                level="critical",
                user_id=user_id,
                error=str(e)
            )

            raise ValueError("Unable to create session")

    # =====================================================
    # GET SESSION
    # =====================================================

    def get_session(self, refresh_token: str):

        try:

            token_hash = hash_token(refresh_token)

            session = (
                self.db.query(UserSession)
                .filter(
                    UserSession.refresh_token_hash == token_hash,
                    UserSession.is_revoked == False,
                    UserSession.is_active == True
                )
                .first()
            )

            if not session:
                return None

            # --------------------------------------------------
            # EXPIRED SESSION
            # --------------------------------------------------

            if session.expires_at < datetime.utcnow():

                session.is_revoked = True
                session.revoked_at = datetime.utcnow()

                self.db.commit()

                log_event(
                    "expired_session_revoked",
                    user_id=session.user_id
                )

                return None

            # update activity timestamp
            session.last_used_at = datetime.utcnow()
            self.db.commit()

            return session

        except Exception as e:

            log_event(
                "session_lookup_error",
                level="critical",
                error=str(e)
            )

            return None

    # =====================================================
    # ROTATE REFRESH TOKEN
    # =====================================================

    def rotate_refresh_token(self, session: UserSession):

        try:

            new_refresh_token = create_refresh_token()
            new_hash = hash_token(new_refresh_token)

            session.refresh_token_hash = new_hash
            session.last_used_at = datetime.utcnow()
            session.expires_at = datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS)

            self.db.commit()

            log_event(
                "refresh_token_rotated",
                user_id=session.user_id,
                ip=session.ip_address
            )

            return new_refresh_token

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "refresh_token_rotation_failed",
                level="critical",
                user_id=session.user_id,
                error=str(e)
            )

            raise ValueError("Unable to rotate refresh token")

    # =====================================================
    # LOGOUT (REVOKE SESSION)
    # =====================================================

    def delete_session(self, refresh_token: str):

        try:

            token_hash = hash_token(refresh_token)

            session = (
                self.db.query(UserSession)
                .filter(UserSession.refresh_token_hash == token_hash)
                .first()
            )

            if session:

                session.is_revoked = True
                session.revoked_at = datetime.utcnow()

                self.db.commit()

                log_event(
                    "session_revoked",
                    user_id=session.user_id,
                    ip=session.ip_address
                )

            return True

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "session_revoke_failed",
                level="critical",
                error=str(e)
            )

            return False

    # =====================================================
    # REVOKE ALL USER SESSIONS
    # =====================================================

    def delete_user_sessions(self, user_id: int):

        try:

            (
                self.db.query(UserSession)
                .filter(UserSession.user_id == user_id)
                .update(
                    {
                        "is_revoked": True,
                        "revoked_at": datetime.utcnow()
                    },
                    synchronize_session=False
                )
            )

            self.db.commit()

            log_event(
                "all_sessions_revoked",
                user_id=user_id
            )

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "session_revoke_failed",
                level="critical",
                user_id=user_id,
                error=str(e)
            )

    # =====================================================
    # LIST USER SESSIONS
    # =====================================================

    def list_user_sessions(self, user_id: int):

        try:

            sessions = (
                self.db.query(UserSession)
                .filter(
                    UserSession.user_id == user_id,
                    UserSession.is_revoked == False
                )
                .order_by(UserSession.created_at.desc())
                .all()
            )

            return sessions

        except Exception as e:

            log_event(
                "session_list_error",
                level="critical",
                user_id=user_id,
                error=str(e)
            )

            return []