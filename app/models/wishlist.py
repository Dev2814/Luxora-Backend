"""
Wishlist Model
==============

Represents a user's wishlist container.

Purpose
-------
• Each user has a single wishlist
• Stores user-specific saved products
• Parent entity for WishlistItems

Architecture
------------
User
   └── Wishlist
          └── WishlistItems
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


class Wishlist(Base):
    """
    Wishlist container for a user.

    One-to-one relationship with User.
    """

    __tablename__ = "wishlists"

    # --------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------

    id = Column(Integer, primary_key=True, index=True)

    # --------------------------------------------------
    # USER RELATIONSHIP (1:1)
    # --------------------------------------------------

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # --------------------------------------------------
    # AUDIT TIMESTAMP
    # --------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # --------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------

    user = relationship(
        "User",
        back_populates="wishlist"
    )

    items = relationship(
        "WishlistItem",
        back_populates="wishlist",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )

    # --------------------------------------------------
    # INDEXES
    # --------------------------------------------------

    __table_args__ = (
        Index("idx_wishlist_user", "user_id"),
    )