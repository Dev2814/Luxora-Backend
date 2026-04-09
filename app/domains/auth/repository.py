"""
Auth Repository

Handles all database operations related to authentication.

Enterprise architecture rule:
Service layer MUST NOT directly access the database.
"""

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User
from app.models.user_sessions import UserSession
from app.models.customer_profile import CustomerProfile
from app.models.vendor_profile import VendorProfile
from app.models.login_history import LoginHistory


class AuthRepository:

    def __init__(self, db: Session):
        self.db = db

    # =====================================================
    # USER QUERIES
    # =====================================================

    def get_user_by_email(self, email: str) -> Optional[User]:

        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_user_by_phone(self, phone: str) -> Optional[User]:

        return (
            self.db.query(User)
            .filter(User.phone == phone)
            .first()
        )

    def get_user_by_id(self, user_id: int) -> Optional[User]:

        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    # =====================================================
    # CREATE USER
    # =====================================================

    def create_user(self, user: User) -> User:

        try:

            self.db.add(user)
            self.db.flush()

            return user

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # =====================================================
    # CREATE CUSTOMER PROFILE
    # =====================================================

    def create_customer_profile(self, profile: CustomerProfile) -> CustomerProfile:

        try:

            self.db.add(profile)
            self.db.flush()

            return profile

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # =====================================================
    # CREATE VENDOR PROFILE
    # =====================================================

    def create_vendor_profile(self, profile: VendorProfile) -> VendorProfile:

        try:

            self.db.add(profile)
            self.db.flush()

            return profile

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # =====================================================
    # GET VENDOR PROFILE
    # =====================================================

    def get_vendor_profile(self, user_id: int) -> Optional[VendorProfile]:

        return (
            self.db.query(VendorProfile)
            .filter(VendorProfile.user_id == user_id)
            .first()
        )    
    
    # =====================================================
    # GET VENDOR PROFILE BY GST NUMBER
    # =====================================================

    def get_vendor_by_gst(self, gst_number: str):

        return (
            self.db.query(VendorProfile)
            .filter(VendorProfile.gst_number == gst_number)
            .first()
        )

    # =====================================================
    # LOGIN HISTORY
    # =====================================================

    def create_login_history(self, record: LoginHistory) -> LoginHistory:

        try:

            self.db.add(record)
            self.db.commit()

            return record

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # =====================================================
    # USER SECURITY UPDATES
    # =====================================================

    def update_user(self, user: User):

        try:

            self.db.add(user)
            self.db.commit()

        except SQLAlchemyError:
            self.db.rollback()
            raise

    # =====================================================
    # SESSION MANAGEMENT
    # =====================================================

    def create_session(self, session: UserSession) -> UserSession:

        try:

            self.db.add(session)
            self.db.commit()

            return session

        except SQLAlchemyError:
            self.db.rollback()
            raise

    def get_session_by_refresh_hash(self, token_hash: str) -> Optional[UserSession]:

        return (
            self.db.query(UserSession)
            .filter(UserSession.refresh_token_hash == token_hash)
            .first()
        )

    def delete_session(self, session: UserSession):

        try:

            self.db.delete(session)
            self.db.commit()

        except SQLAlchemyError:
            self.db.rollback()
            raise

    def delete_user_sessions(self, user_id: int):

        try:

            (
                self.db.query(UserSession)
                .filter(UserSession.user_id == user_id)
                .delete(synchronize_session=False)
            )

            self.db.commit()

        except SQLAlchemyError:
            self.db.rollback()
            raise