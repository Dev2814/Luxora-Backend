"""
Coupon Service
==============

Handles business logic for coupon system.

Responsibilities
----------------
• Validate coupon
• Prevent abuse (limits, expiry)
• Calculate discount
• Apply coupon to order
• Record usage

Design Principles
-----------------
• Business logic ONLY
• Uses repository layer
• Transaction-safe
• Optimized for checkout flow
• Scalable for high traffic

Architecture
------------
Routes → Service → Repository → DB
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from app.domains.coupons.repository import CouponRepository
from app.models.coupon import Coupon
from app.core.logger import log_event


class CouponService:
    """
    Service responsible for coupon operations.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = CouponRepository(db)

    # ======================================================
    # CREATE COUPON (ADMIN)
    # ======================================================

    def create_coupon(self, payload):
        """
        Admin creates a coupon.

        Rules:
        • Code must be unique
        • Valid date range
        • Proper normalization
        """

        try:

            # ---------------------------------------------
            # NORMALIZE CODE
            # ---------------------------------------------
            code = payload.code.upper()

            # ---------------------------------------------
            # DUPLICATE CHECK
            # ---------------------------------------------
            existing = self.repo.get_by_code(code)

            if existing:
                raise ValueError("Coupon code already exists")

            # ---------------------------------------------
            # DATE VALIDATION
            # ---------------------------------------------
            if payload.valid_from >= payload.valid_until:
                raise ValueError("Invalid coupon date range")

            # ---------------------------------------------
            # TYPE VALIDATION
            # ---------------------------------------------
            if payload.type not in ["percentage", "flat"]:
                raise ValueError("Invalid coupon type")

            # ---------------------------------------------
            # CREATE OBJECT
            # ---------------------------------------------
            coupon = Coupon(
                code=code,
                description=payload.description,
                type=payload.type,
                value=payload.value,
                max_discount=payload.max_discount,
                min_order_amount=payload.min_order_amount,
                usage_limit=payload.usage_limit,
                usage_per_user=payload.usage_per_user,
                valid_from=payload.valid_from,
                valid_until=payload.valid_until,
                is_active=True,
                used_count=0
            )

            # ---------------------------------------------
            # SAVE
            # ---------------------------------------------
            self.repo.create_coupon(coupon)

            self.db.commit()

            log_event(
                "coupon_created",
                code=code,
                type=payload.type,
                value=payload.value
            )

            return {"message": "Coupon created successfully"}

        except ValueError:
            raise

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "coupon_create_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Failed to create coupon")

    # ======================================================
    # VALIDATE COUPON
    # ======================================================

    def validate_coupon(
        self,
        user_id: int,
        code: str,
        order_amount: float
    ) -> Coupon:
        """
        Validate coupon before applying.

        Checks:
        • Exists
        • Active
        • Valid date range
        • Min order amount
        • Usage limits
        """

        coupon = self.repo.get_by_code(code)

        if not coupon:
            raise ValueError("Invalid coupon code")

        # --------------------------------------------------
        # ACTIVE + TIME VALIDATION
        # --------------------------------------------------

        if not self.repo.is_valid_now(coupon):
            raise ValueError("Coupon expired or inactive")

        # --------------------------------------------------
        # MIN ORDER VALUE
        # --------------------------------------------------

        if coupon.min_order_amount and order_amount < float(coupon.min_order_amount):
            raise ValueError(
                f"Minimum order amount is {coupon.min_order_amount}"
            )

        # --------------------------------------------------
        # GLOBAL USAGE LIMIT
        # --------------------------------------------------

        if coupon.usage_limit is not None:
            total_usage = coupon.used_count  # fast path

            if total_usage >= coupon.usage_limit:
                raise ValueError("Coupon usage limit reached")

        # --------------------------------------------------
        # PER USER LIMIT
        # --------------------------------------------------

        if coupon.usage_per_user is not None:
            user_usage = self.repo.get_user_usage(user_id, coupon.id)

            if user_usage >= coupon.usage_per_user:
                raise ValueError("You have already used this coupon")

        return coupon

    # ======================================================
    # CALCULATE DISCOUNT
    # ======================================================

    def calculate_discount(
        self,
        coupon: Coupon,
        order_amount: float
    ) -> float:
        """
        Calculate discount amount.

        Supports:
        • Percentage
        • Flat
        • Max discount cap
        """

        if coupon.type == "percentage":
            discount = order_amount * (float(coupon.value) / 100)

        elif coupon.type == "flat":
            discount = float(coupon.value)

        else:
            discount = 0

        # --------------------------------------------------
        # APPLY MAX DISCOUNT CAP
        # --------------------------------------------------

        if coupon.max_discount:
            discount = min(discount, float(coupon.max_discount))

        return round(discount, 2)

    # ======================================================
    # APPLY COUPON (MAIN FUNCTION)
    # ======================================================

    def apply_coupon(
        self,
        user_id: int,
        code: str,
        order_amount: float
    ):
        """
        Validate and calculate discount.

        Used BEFORE order creation.
        """

        try:

            coupon = self.validate_coupon(
                user_id=user_id,
                code=code,
                order_amount=order_amount
            )

            discount = self.calculate_discount(coupon, order_amount)

            return {
                "coupon_id": coupon.id,
                "code": coupon.code,
                "discount": discount,
                "final_amount": round(order_amount - discount, 2)
            }

        except ValueError:
            raise

        except Exception as e:

            log_event(
                "coupon_apply_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to apply coupon")

    # ======================================================
    # CONFIRM USAGE (AFTER ORDER SUCCESS)
    # ======================================================

    def confirm_coupon_usage(
        self,
        user_id: int,
        coupon_id: int,
        order_id: int
    ):
        """
        Record coupon usage after successful order.

        IMPORTANT:
        • Should be called ONLY after payment success
        """

        try:

            coupon = self.db.get(Coupon, coupon_id)

            if not coupon:
                raise ValueError("Coupon not found")

            # Create usage record
            self.repo.create_usage(
                user_id=user_id,
                coupon_id=coupon_id,
                order_id=order_id
            )

            # Increment usage counter
            self.repo.increment_used_count(coupon)

            self.db.commit()

            log_event(
                "coupon_used",
                user_id=user_id,
                coupon_id=coupon_id,
                order_id=order_id
            )

        except Exception as e:

            self.db.rollback()

            log_event(
                "coupon_usage_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Failed to record coupon usage")