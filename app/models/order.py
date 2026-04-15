"""
Order Model
===========

Represents a customer order created during checkout.

Purpose
-------
• Stores order-level information
• Links customer to shipping address
• Tracks order status and payment status
• Parent entity for OrderItems

Enterprise Features
-------------------
• Indexed lookups
• Enum-based order status
• Enum-based payment status
• Audit timestamps
• Relationships with user, address, and order items

Architecture
------------
User
   │
   └── Orders
          │
          └── OrderItems
                 │
                 └── ProductVariant
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Enum,
    Numeric,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base

import enum


# ======================================================
# ORDER STATUS ENUM
# ======================================================

class OrderStatus(str, enum.Enum):
    """
    Order lifecycle states.
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ======================================================
# PAYMENT STATUS ENUM
# ======================================================

class PaymentStatus(str, enum.Enum):
    """
    Payment lifecycle states.
    """

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


# ======================================================
# ORDER MODEL
# ======================================================

class Order(Base):
    """
    Represents a customer order created during checkout.
    """

    __tablename__ = "orders"

    # ==================================================
    # PRIMARY KEY
    # ==================================================

    id = Column(Integer, primary_key=True, index=True)

    # ==================================================
    # USER RELATION
    # ==================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ==================================================
    # SHIPPING ADDRESS
    # ==================================================

    address_id = Column(
        Integer,
        ForeignKey("user_addresses.id"),
        nullable=False
    )

    # ==================================================
    # ORDER STATUS
    # ==================================================

    status = Column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False
    )

    # ==================================================
    # PAYMENT STATUS
    # ==================================================

    payment_status = Column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False
    )

    # ==================================================
    # TOTAL AMOUNT
    # ==================================================

    total_amount = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    # ==================================================
    # AUDIT TIMESTAMPS
    # ==================================================

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

    status_updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        # onupdate=func.now(),
        nullable=False,
        index=True
    )

    # ==================================================
    # RELATIONSHIPS
    # ==================================================

    user = relationship(
        "User",
        back_populates="orders",
        passive_deletes=True
    )

    address = relationship(
        "UserAddress",
        back_populates="orders"
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    payments = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    invoice = relationship(
        "Invoice",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )

    coupon_usage = relationship(
        "CouponUsage",
        back_populates="order",
        uselist=False
    )

    timeline = relationship(
        "OrderTimeline",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="OrderTimeline.created_at.asc()"
    )

    # ==================================================
    # INDEXES
    # ==================================================

    __table_args__ = (
        Index("idx_order_user", "user_id"),
    )