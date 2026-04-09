"""
Coupon Model
============

Represents a promotional discount code.

Design Goals
------------
• Support percentage & flat discounts
• Prevent abuse (global + per-user limits)
• Enable marketing campaigns
• Time-based activation
• Scalable & index-optimized

Architecture
------------
Coupon → Applied during checkout → CouponUsage
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Numeric,
    Enum,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
import enum


# =========================================================
# ENUM: COUPON TYPE
# =========================================================

class CouponType(str, enum.Enum):
    """
    Defines discount type.
    """
    percentage = "percentage"
    flat = "flat"


class Coupon(Base):
    """
    Represents a discount coupon.

    Example:
        code = "NEWUSER10"
        type = percentage
        value = 10 (10%)
    """

    __tablename__ = "coupons"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(Integer, primary_key=True, index=True)

    # =========================================================
    # COUPON INFO
    # =========================================================

    code = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )

    description = Column(
        String(255),
        nullable=True
    )

    # =========================================================
    # DISCOUNT CONFIGURATION
    # =========================================================

    type = Column(
        Enum(CouponType),
        nullable=False
    )

    # percentage OR flat value
    value = Column(
        Numeric(10, 2),
        nullable=False
    )

    # Max discount cap (for percentage)
    max_discount = Column(
        Numeric(10, 2),
        nullable=True
    )

    # Minimum cart value required
    min_order_amount = Column(
        Numeric(10, 2),
        nullable=True
    )

    # =========================================================
    # USAGE LIMITS
    # =========================================================

    # Total usage limit
    usage_limit = Column(
        Integer,
        nullable=True
    )

    # Per user usage limit
    usage_per_user = Column(
        Integer,
        nullable=True
    )

    # Track total usage count
    used_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    # =========================================================
    # VALIDITY WINDOW
    # =========================================================

    valid_from = Column(
        DateTime(timezone=True),
        nullable=False
    )

    valid_until = Column(
        DateTime(timezone=True),
        nullable=False
    )

    # =========================================================
    # STATUS FLAGS
    # =========================================================

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # Soft delete (optional future)
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    # =========================================================
    # AUDIT TIMESTAMPS
    # =========================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # =========================================================
    # RELATIONSHIPS
    # =========================================================

    usages = relationship(
        "CouponUsage",
        back_populates="coupon",
        cascade="all, delete-orphan"
    )

    # =========================================================
    # INDEXES (PERFORMANCE)
    # =========================================================

    __table_args__ = (

        # Fast lookup by code (critical)
        Index("idx_coupon_code", "code"),

        # Active + valid filtering
        Index("idx_coupon_active", "is_active"),

        # Validity window queries
        Index("idx_coupon_validity", "valid_from", "valid_until"),

        # Prevent duplicate codes (extra safety)
        UniqueConstraint("code", name="uq_coupon_code"),
    )