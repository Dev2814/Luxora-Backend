"""
User Service

Handles user profile and session management.
Enterprise features:
- structured logging
- safe error handling
- audit events
- idempotent session revocation
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from fastapi import HTTPException, status

from app.domains.users.repository import UserRepository
from app.api.v1.users.schemas import (
    UserProfileResponse,
    UpdateProfileRequest,
    SessionResponse
    )
from app.core.logger import log_event


class UserService:

    def __init__(self, db: Session):

        self.db = db
        self.repo = UserRepository(db)

    # =====================================================
    # GET USER PROFILE
    # =====================================================

    def get_profile(self, user_id: int):

        try:

            user = self.repo.get_user(user_id)

            if not user:

                log_event(
                    "user_profile_not_found",
                    level="warning",
                    user_id=user_id
                )

                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            profile = self.repo.get_customer_profile(user_id)

            log_event(
                "user_profile_viewed",
                user_id=user_id
            )

            return UserProfileResponse(
                id=user.id,
                email=user.email,
                phone=user.phone,
                role=user.role,
                status=user.status,
                full_name=profile.full_name if profile else None,
                gender=profile.gender if profile else None,
                date_of_birth=profile.date_of_birth if profile else None,
            )

        except HTTPException:
            raise

        except Exception as e:

            log_event(
                "user_profile_fetch_error",
                level="critical",
                user_id=user_id,
                error=str(e)
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user profile"
            )

    # =====================================================
    # UPDATE PROFILE
    # =====================================================

    def update_profile(self, user_id: int, payload):

        try:
            user = self.repo.get_user(user_id)
            profile = self.repo.get_customer_profile(user_id)

            if not profile or not user:
                raise HTTPException(status_code=404, detail="Profile not found")

            data = payload.model_dump(exclude_unset=True)

            # -------------------------------
            # SPLIT DATA
            # -------------------------------
            profile_data = {}
            user_data = {}

            for key, value in data.items():
                if key in ["full_name", "gender", "date_of_birth"]:
                    profile_data[key] = value
                elif key == "phone":
                    user_data[key] = value

            # -------------------------------
            # UPDATE PROFILE TABLE
            # -------------------------------
            self.repo.update_customer_profile(profile, profile_data)

            # -------------------------------
            # UPDATE USER TABLE
            # -------------------------------
            if user_data:
                self.repo.update_user(user, user_data)

            self.db.commit()

            return profile

        except Exception as e:
            self.db.rollback()
            raise

    # =====================================================
    # GET USER SESSIONS
    # =====================================================

    
    def get_sessions(self, user_id: int):

        try:

            sessions = self.repo.get_user_sessions(user_id)

            log_event(
                "user_sessions_viewed",
                user_id=user_id,
                session_count=len(sessions)
            )

            return sessions

        except Exception as e:

            log_event(
                "user_sessions_fetch_error",
                level="critical",
                user_id=user_id,
                error=str(e)
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch sessions"
            )

    # =====================================================
    # REVOKE SESSION
    # =====================================================

    def revoke_session(self, session_id: int):

        """
        Enterprise safe session revoke
        Idempotent delete pattern
        """

        try:

            session = self.repo.delete_session(session_id)

            # ---------------------------------------------
            # SESSION NOT FOUND
            # ---------------------------------------------

            if not session:

                log_event(
                    "session_revoke_not_found",
                    level="warning",
                    session_id=session_id
                )

                return {
                    "message": "Session already revoked or not found"
                }

            self.db.commit()

            log_event(
                "session_revoked",
                session_id=session_id
            )

            return {
                "message": "Session revoked successfully"
            }

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "session_revoke_database_error",
                level="critical",
                session_id=session_id,
                error=str(e)
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session revoke failed"
            )

        except Exception as e:

            log_event(
                "session_revoke_error",
                level="critical",
                session_id=session_id,
                error=str(e)
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error during session revoke"
            )