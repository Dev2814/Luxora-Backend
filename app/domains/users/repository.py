"""
User Repository

Handles database access for user domain.
"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.customer_profile import CustomerProfile
from app.models.user_sessions import UserSession


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    # --------------------------------------------------
    # GET USER BY ID
    # --------------------------------------------------

    def get_user(self, user_id: int):

        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    # --------------------------------------------------
    # GET CUSTOMER PROFILE
    # --------------------------------------------------

    def get_customer_profile(self, user_id: int):

        return (
            self.db.query(CustomerProfile)
            .filter(CustomerProfile.user_id == user_id)
            .first()
        )

    # --------------------------------------------------
    # UPDATE CUSTOMER PROFILE
    # --------------------------------------------------

    def update_customer_profile(self, profile, data: dict):

        for key, value in data.items():
            setattr(profile, key, value)

        self.db.commit()
        self.db.refresh(profile)

        return profile
    
    
    # --------------------------------------------------
    # UPDATE USER (NEW - REQUIRED)
    # --------------------------------------------------

    def update_user(self, user, data: dict):

        for key, value in data.items():
            setattr(user, key, value)

        self.db.commit()         
        self.db.refresh(user)

        return user

    # --------------------------------------------------
    # GET USER SESSIONS
    # --------------------------------------------------

    def get_user_sessions(self, user_id: int):

        return (
            self.db.query(UserSession)
            .filter(UserSession.user_id == user_id)
            .all()
        )

    # --------------------------------------------------
    # DELETE SESSION
    # --------------------------------------------------

    def delete_session(self, session_id: int):

        session = (
            self.db.query(UserSession)
            .filter(UserSession.id == session_id)
            .first()
        )

        if session:
            self.db.delete(session)
            self.db.commit()

        return session