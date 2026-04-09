"""
Wishlist Item Model
===================

Represents a product saved by a user.

Purpose
-------
• Stores individual wishlist entries
• Links wishlist to product variants
• Prevent duplicate entries

Architecture
------------
Wishlist
   └── WishlistItems
          └── ProductVariant
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class WishlistItem(Base):
    """
    Represents a product saved in a wishlist.
    """

    __tablename__ = "wishlist_items"

    # --------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------

    id = Column(Integer, primary_key=True, index=True)

    # --------------------------------------------------
    # RELATIONS
    # --------------------------------------------------

    wishlist_id = Column(
        Integer,
        ForeignKey("wishlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    variant_id = Column(
        Integer,
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # --------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # --------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------

    wishlist = relationship(
        "Wishlist",
        back_populates="items",
        lazy="selectin" 
    )

    variant = relationship(
        "ProductVariant",
        back_populates="wishlist_items",
        passive_deletes=True,
        lazy="joined" 
    )

    # --------------------------------------------------
    # CONSTRAINTS
    # --------------------------------------------------

    __table_args__ = (
        UniqueConstraint("wishlist_id", "variant_id", name="uq_wishlist_variant"),
        Index("idx_wishlist_item_variant", "variant_id"),
        Index("idx_wishlist_lookup", "wishlist_id", "variant_id"), 
    )