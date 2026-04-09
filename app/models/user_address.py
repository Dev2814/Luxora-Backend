"""
User Address Model
==================

Stores address information for users.

Purpose
-------
• Allow users to store multiple shipping / billing addresses
• Used during checkout and order placement
• Supports default address selection

Enterprise Features
-------------------
• Multiple addresses per user
• Default address support
• Indexed user lookups
• Audit timestamps
• Cascade deletion with user

Architecture
------------
User
   └── UserAddress
           └── Orders.address_id
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserAddress(Base):
    """
    Represents a saved address for a user.

    A user can store multiple addresses such as:
    - Home
    - Office
    - Other
    """

    __tablename__ = "user_addresses"

    # ======================================================
    # PRIMARY KEY
    # ======================================================

    id = Column(Integer, primary_key=True, index=True)

    # ======================================================
    # USER RELATION
    # ======================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ======================================================
    # ADDRESS LABEL
    # ======================================================

    label = Column(
        String(50),
        nullable=True
    )
    # Example: Home, Office

    # ======================================================
    # CONTACT INFO
    # ======================================================

    full_name = Column(
        String(255),
        nullable=False
    )

    phone_number = Column(
        String(20),
        nullable=False
    )

    # ======================================================
    # ADDRESS DETAILS
    # ======================================================

    address_line1 = Column(
        String(255),
        nullable=False
    )

    address_line2 = Column(
        String(255),
        nullable=True
    )

    city = Column(
        String(100),
        nullable=False
    )

    state = Column(
        String(100),
        nullable=False
    )

    postal_code = Column(
        String(20),
        nullable=False
    )

    country = Column(
        String(100),
        nullable=False,
        default="India"
    )

    # ======================================================
    # DEFAULT ADDRESS FLAG
    # ======================================================

    is_default = Column(
        Boolean,
        default=False
    )

    # ======================================================
    # AUDIT TIMESTAMPS
    # ======================================================

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

    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    user = relationship(
        "User",
        back_populates="addresses",
        passive_deletes=True
    )

    orders = relationship(
        "Order",
        back_populates="address",
        # passive_deletes=True
    )

    # ======================================================
    # INDEXES
    # ======================================================

    __table_args__ = (
        Index("idx_user_address_user", "user_id"),
    )