"""
Payment Model
=============

Stores payment transaction details for orders.

Purpose
-------
• Track payment status
• Store Stripe transaction information
• Link payments to orders

Architecture
------------
Order
   │
   └── Payment
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Numeric,
    Enum,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base

import enum


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
# PAYMENT MODEL
# ======================================================

class Payment(Base):
    """
    Represents a payment transaction for an order.
    """

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    # --------------------------------------------------
    # ORDER RELATION
    # --------------------------------------------------

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # --------------------------------------------------
    # PAYMENT AMOUNT
    # --------------------------------------------------

    amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    # --------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------

    payment_method = Column(
        String(50),
        nullable=False,
        default="stripe"
    )

    # --------------------------------------------------
    # PAYMENT STATUS
    # --------------------------------------------------

    status = Column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False
    )

    # --------------------------------------------------
    # STRIPE TRANSACTION DATA
    # --------------------------------------------------

    transaction_id = Column(
        String(255),
        nullable=True
    )

    stripe_payment_intent = Column(
        String(255),
        nullable=True,
        index=True,
    )

    # --------------------------------------------------
    # AUDIT TIMESTAMP
    # --------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # --------------------------------------------------
    # RELATIONSHIP
    # --------------------------------------------------

    order = relationship(
        "Order", 
        back_populates="payments",
        passive_deletes=True,
    )

    # --------------------------------------------------
    # INDEXES
    # --------------------------------------------------

    __table_args__ = (
        Index("idx_payment_order", "order_id"),
    )