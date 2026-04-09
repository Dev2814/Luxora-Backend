"""
Cart Item Model
===============

Represents a product variant inside a customer's cart.

Purpose
-------
• Stores items added to the cart
• Connects Cart with ProductVariant
• Tracks quantity selected by the customer

Enterprise Features
-------------------
• Variant-based cart design
• Indexed lookups
• Cascade deletion when cart is removed
• Audit timestamps

Architecture
------------
Cart
   │
   └── CartItems
          │
          └── ProductVariant
                 │
                 └── Inventory
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


class CartItem(Base):
    """
    Represents an item inside a shopping cart.
    """

    __tablename__ = "cart_items"

    # ==================================================
    # PRIMARY KEY
    # ==================================================

    id = Column(Integer, primary_key=True, index=True)

    # ==================================================
    # CART RELATION
    # ==================================================

    cart_id = Column(
        Integer,
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ==================================================
    # PRODUCT VARIANT RELATION
    # ==================================================

    variant_id = Column(
        Integer,
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ==================================================
    # QUANTITY
    # ==================================================

    quantity = Column(
        Integer,
        nullable=False,
        default=1
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

    cart = relationship(
        "Cart",
        back_populates="items"
    )

    variant = relationship(
        "ProductVariant"
    )

    # ==================================================
    # CONSTRAINTS
    # ==================================================

    __table_args__ = (

        # Prevent duplicate variant in same cart
        UniqueConstraint(
            "cart_id",
            "variant_id",
            name="uq_cart_variant"
        ),

        Index("idx_cart_item_cart", "cart_id"),
        Index("idx_cart_item_variant", "variant_id"),
    )