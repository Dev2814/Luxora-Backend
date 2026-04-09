"""
Cart Model
==========

Represents a customer's active shopping cart.

Purpose
-------
• Each customer has one active cart
• Stores items the customer intends to purchase
• Works together with CartItem table

Enterprise Features
-------------------
• One-to-one relation with user
• Audit timestamps
• Indexed user lookup
• Cascade deletion of cart items

Architecture
------------
User
   │
   └── Cart
          │
          └── CartItems
                 │
                 └── ProductVariant
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Cart(Base):
    """
    Shopping cart associated with a user.
    """

    __tablename__ = "carts"

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
        unique=True,  # one cart per user
        index=True
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

    # ==================================================
    # RELATIONSHIPS
    # ==================================================

    user = relationship(
        "User",
        back_populates="cart",
        passive_deletes=True
    )

    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan"
    )

    # ==================================================
    # INDEXES
    # ==================================================

    __table_args__ = (
        Index("idx_cart_user", "user_id"),
    )