"""
Order Timeline Model
====================

Tracks the lifecycle history of an order.

Purpose
-------
• Maintain complete audit trail of order status changes
• Enable timeline UI (Amazon-style order tracking)
• Support analytics (delivery time, delays)
• Debugging and operational visibility

Architecture
------------
Order
   └── OrderTimeline (1:N)

Example Flow
------------
pending → confirmed → shipped → delivered

Each transition is stored as a new record.

Enterprise Features
-------------------
• Immutable event log (append-only)
• Indexed for fast retrieval
• Supports future event types (e.g. "out_for_delivery")
• Audit timestamp tracking
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class OrderTimeline(Base):
    """
    Represents a single status event in an order lifecycle.

    Example:
    Order #101:
        pending     → 10:00 AM
        confirmed   → 10:05 AM
        shipped     → 02:00 PM
    """

    __tablename__ = "order_timeline"

    # ==================================================
    # PRIMARY KEY
    # ==================================================
    id = Column(Integer, primary_key=True, index=True)

    # ==================================================
    # ORDER RELATIONSHIP
    # ==================================================
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ==================================================
    # STATUS SNAPSHOT
    # ==================================================
    status = Column(
        String(50),
        nullable=False,
        index=True
    )

    # ==================================================
    # EVENT METADATA (FUTURE READY)
    # ==================================================
    note = Column(
        String(255),
        nullable=True
    )

    # Example:
    # "Order confirmed by vendor"
    # "Shipped via Delhivery"

    # ==================================================
    # TIMESTAMP
    # ==================================================
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # ==================================================
    # RELATIONSHIPS
    # ==================================================
    order = relationship(
        "Order",
        back_populates="timeline",
        passive_deletes=True
    )

    # ==================================================
    # DATABASE INDEXES (PERFORMANCE)
    # ==================================================
    __table_args__ = (
        # Fast lookup per order timeline
        Index("idx_timeline_order", "order_id"),

        # Status-based filtering (analytics)
        Index("idx_timeline_status", "status"),

        # Time-based queries
        Index("idx_timeline_created", "created_at"),
    )

    # ==================================================
    # DEBUG REPRESENTATION
    # ==================================================
    def __repr__(self):
        return f"<OrderTimeline order_id={self.order_id} status={self.status}>"