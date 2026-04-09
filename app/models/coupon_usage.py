"""
Coupon Usage Model
==================

Tracks usage of coupons by users.

Design Goals
------------
• Prevent coupon abuse
• Track per-user usage
• Enable analytics (campaign performance)
• Ensure one usage per order
• Support auditing

Architecture
------------
Coupon → CouponUsage → Order → User
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class CouponUsage(Base):
    """
    Represents a single usage of a coupon by a user.

    Example:
        User applies coupon "NEWUSER10" on Order #123
    """

    __tablename__ = "coupon_usages"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(Integer, primary_key=True, index=True)

    # =========================================================
    # RELATIONS
    # =========================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    coupon_id = Column(
        Integer,
        ForeignKey("coupons.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 🔥 IMPORTANT: Link with order
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # =========================================================
    # TIMESTAMP
    # =========================================================

    used_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =========================================================
    # RELATIONSHIPS
    # =========================================================

    user = relationship(
        "User",
        back_populates="coupon_usages"
    )

    coupon = relationship(
        "Coupon",
        back_populates="usages"
    )

    order = relationship(
        "Order",
        back_populates="coupon_usage"
    )

    # =========================================================
    # CONSTRAINTS
    # =========================================================

    __table_args__ = (

        # ❌ Prevent same user using same coupon multiple times on same order
        UniqueConstraint(
            "user_id",
            "coupon_id",
            "order_id",
            name="uq_user_coupon_order"
        ),

        # Fast lookup for user usage count
        Index("idx_coupon_usage_user", "user_id"),

        # Fast lookup for coupon usage count
        Index("idx_coupon_usage_coupon", "coupon_id"),
    )