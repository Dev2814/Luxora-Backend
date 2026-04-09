"""
Admin Repository

Handles all database interactions for the admin module.

Architecture:
Service → Repository → Database

Responsibilities:
- Vendor moderation queries
- Brand management queries
- User management queries
- Platform analytics queries
- Admin activity logging
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.models.vendor_profile import VendorProfile, VendorStatus
from app.models.customer_profile import CustomerProfile
from app.models.brand import Brand
from app.models.user import User
from app.models.admin_activity_log import AdminActivityLog


class AdminRepository:

    def __init__(self, db: Session):
        self.db = db

    # ==================================================
    # GENERIC SAVE
    # ==================================================

    def save(self, entity):
        """
        Generic method to persist an entity.
        """
        self.db.add(entity)

    # ==================================================
    # VENDOR OPERATIONS
    # ==================================================

    def get_vendor_by_id(self, vendor_id: int) -> Optional[VendorProfile]:
        """
        Fetch a vendor profile by ID.
        """

        return (
            self.db.query(VendorProfile)
            .filter(VendorProfile.id == vendor_id)
            .first()
        )

    def get_all_vendors(self) -> List[VendorProfile]:
        """
        Fetch all vendor profiles.
        """

        return self.db.query(VendorProfile).all()

    def get_pending_vendors(self) -> List[VendorProfile]:
        """
        Fetch vendors awaiting admin approval.
        """

        return (
            self.db.query(VendorProfile)
            .filter(VendorProfile.verification_status == VendorStatus.PENDING)
            .all()
        )

    # --------------------------------------------------

    def count_total_vendors(self) -> int:
        """
        Count total vendors on the platform.
        """

        return self.db.query(func.count(VendorProfile.id)).scalar()
    
    # -------------------------------------------------
    
    def count_total_Buyers(self) -> int:
        """
        Count total Customers on the platform.
        """

        return self.db.query(func.count(CustomerProfile.id)).scalar()
    
    # -------------------------------------------------

    def count_approved_vendors(self) -> int:
        """
        Count approved vendors.
        """

        return (
            self.db.query(func.count(VendorProfile.id))
            .filter(VendorProfile.verification_status == VendorStatus.APPROVED)
            .scalar()
        )

    def count_pending_vendors(self) -> int:
        """
        Count vendors awaiting approval.
        """

        return (
            self.db.query(func.count(VendorProfile.id))
            .filter(VendorProfile.verification_status == VendorStatus.PENDING)
            .scalar()
        )

    # ==================================================
    # BRAND OPERATIONS
    # ==================================================

    def get_brand_by_name(self, name: str) -> Optional[Brand]:
        """
        Fetch brand by name.
        """

        return (
            self.db.query(Brand)
            .filter(func.lower(Brand.name) == name.lower())
            .first()
        )

    def get_brand_by_id(self, brand_id: int) -> Optional[Brand]:
        """
        Fetch brand by ID.
        """

        return (
            self.db.query(Brand)
            .filter(Brand.id == brand_id)
            .first()
        )

    def create_brand(self, brand: Brand):
        """
        Persist new brand.
        """

        self.db.add(brand)

    def list_brands(self) -> List[Brand]:
        """
        Fetch all platform brands.
        """

        return self.db.query(Brand).all()

    def delete_brand(self, brand: Brand):
        """
        Remove brand from database.
        """

        self.db.delete(brand)

    # ==================================================
    # USER OPERATIONS
    # ==================================================

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Fetch user by ID.
        """

        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def count_total_users(self) -> int:
        """
        Count total registered users.
        """

        return self.db.query(func.count(User.id)).scalar()

    # ==================================================
    # ADMIN ACTIVITY LOGGING
    # ==================================================

    def log_admin_activity(self, log: AdminActivityLog):
        """
        Store admin activity log.
        """

        self.db.add(log)

    # ==================================================
    # TRANSACTION CONTROL
    # ==================================================

    def commit(self):
        """
        Commit database transaction.
        """

        self.db.commit()

    def rollback(self):
        """
        Rollback transaction on failure.
        """

        self.db.rollback()