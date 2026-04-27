"""
Notification Model
==================

Handles system notifications for users (vendors, customers, admins).

Use Cases:
----------
• Vendor gets notified when new order is placed
• Customer gets order updates
• Admin gets system alerts

Design Principles:
------------------
• Scalable (supports millions of notifications)
• Role-based targeting (vendor/customer/admin)
• Read/unread tracking
• Extendable for push/email/websocket

Architecture:
-------------
User → Notification
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    DateTime,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Notification(Base):
    """
    Represents a system notification.

    Example:
    --------
    "New order received for your product"
    """

    __tablename__ = "notifications"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(Integer, primary_key=True, index=True)

    # =========================================================
    # TARGET USER (WHO RECEIVES)
    # =========================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # =========================================================
    # NOTIFICATION CONTENT
    # =========================================================

    title = Column(
        String(255),
        nullable=False
    )

    message = Column(
        String(500),
        nullable=False
    )

    # =========================================================
    # RELATED ENTITY (OPTIONAL)
    # =========================================================

    # Example: order_id, product_id etc.
    reference_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    reference_type = Column(
        String(50),
        nullable=True
    )

    # =========================================================
    # STATUS
    # =========================================================

    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    read_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    # =========================================================
    # TIMESTAMPS
    # =========================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # =========================================================
    # RELATIONSHIPS
    # =========================================================

    user = relationship(
        "User",
        back_populates="notifications"
    )

    # =========================================================
    # DATABASE INDEXES
    # =========================================================

    __table_args__ = (

        # Fast lookup for user notifications
        Index("idx_notification_user", "user_id"),

        # Filter unread notifications quickly
        Index("idx_notification_unread", "is_read"),

        # Sort by latest
        Index("idx_notification_created", "created_at"),
    )