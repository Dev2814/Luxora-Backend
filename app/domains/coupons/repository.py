"""
Coupon Repository
=================

Handles all database operations related to coupons.

Responsibilities
----------------
• Fetch coupon by code
• Validate coupon availability
• Track usage counts
• Get user usage count
• Create coupon usage entry

Design Principles
-----------------
• NO business logic
• Pure DB access layer
• Optimized queries
• Scalable for high traffic

Architecture
------------
Service → Repository → Database
"""

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime

from app.models.coupon import Coupon
from app.models.coupon_usage import CouponUsage


class CouponRepository:
    """
    Repository layer for coupon operations.
    """

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # CREATE COUPON (ADMIN)
    # ======================================================

    def create_coupon(self, coupon: Coupon) -> Coupon:
        """
        Create a new coupon.

        Used by admin panel.
        """

        self.db.add(coupon)
        self.db.flush()
        return coupon
    
    # ======================================================
    # GET COUPON BY CODE
    # ======================================================

    def get_by_code(self, code: str) -> Optional[Coupon]:
        """
        Fetch coupon using coupon code.

        Case-insensitive lookup (important for UX).
        """

        stmt = select(Coupon).where(
            func.lower(Coupon.code) == code.lower(),
            Coupon.is_deleted == False
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # ======================================================
    # VALID COUPON (TIME + STATUS)
    # ======================================================

    def is_valid_now(self, coupon: Coupon) -> bool:
        """
        Check if coupon is currently valid.

        Conditions:
        • Active
        • Within valid date range
        """

        now = datetime.utcnow()

        return (
            coupon.is_active and
            coupon.valid_from <= now <= coupon.valid_until
        )

    # ======================================================
    # GET TOTAL USAGE COUNT
    # ======================================================

    def get_total_usage(self, coupon_id: int) -> int:
        """
        Get total usage count of coupon.
        """

        stmt = (
            select(func.count(CouponUsage.id))
            .where(CouponUsage.coupon_id == coupon_id)
        )

        return self.db.execute(stmt).scalar() or 0

    # ======================================================
    # GET USER USAGE COUNT
    # ======================================================

    def get_user_usage(
        self,
        user_id: int,
        coupon_id: int
    ) -> int:
        """
        Get how many times a user used a coupon.
        """

        stmt = (
            select(func.count(CouponUsage.id))
            .where(
                CouponUsage.user_id == user_id,
                CouponUsage.coupon_id == coupon_id
            )
        )

        return self.db.execute(stmt).scalar() or 0

    # ======================================================
    # CREATE USAGE ENTRY
    # ======================================================

    def create_usage(
        self,
        user_id: int,
        coupon_id: int,
        order_id: int
    ) -> CouponUsage:
        """
        Record coupon usage.

        Called AFTER successful order creation.
        """

        usage = CouponUsage(
            user_id=user_id,
            coupon_id=coupon_id,
            order_id=order_id
        )

        self.db.add(usage)
        self.db.flush()

        return usage

    # ======================================================
    # INCREMENT USAGE COUNT
    # ======================================================

    def increment_used_count(self, coupon: Coupon):
        """
        Increment cached usage count.

        Helps avoid heavy COUNT queries at scale.
        """

        coupon.used_count += 1
        self.db.flush()