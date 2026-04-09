"""
Order Item Model
================

Represents a product variant purchased in an order.

Purpose
-------
• Stores items belonging to an order
• Captures product price at purchase time
• Tracks quantity and subtotal

Enterprise Features
-------------------
• Price snapshot for historical accuracy
• Indexed lookups
• Cascade deletion with order
• Audit timestamps

Architecture
------------
Order
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
    Numeric,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class OrderItem(Base):
    """
    Represents a purchased product variant inside an order.
    """

    __tablename__ = "order_items"

    # ==================================================
    # PRIMARY KEY
    # ==================================================

    id = Column(Integer, primary_key=True, index=True)

    # ==================================================
    # ORDER RELATION
    # ==================================================

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ==================================================
    # PRODUCT VARIANT
    # ==================================================

    variant_id = Column(
        Integer,
        ForeignKey("product_variants.id"),
        nullable=False,
    )

    # ==================================================
    # QUANTITY
    # ==================================================

    quantity = Column(
        Integer,
        nullable=False
    )

    # ==================================================
    # PRICE SNAPSHOT
    # ==================================================

    price_snapshot = Column(
        Numeric(10, 2),
        nullable=False
    )

    # ==================================================
    # SUBTOTAL
    # ==================================================

    subtotal = Column(
        Numeric(10, 2),
        nullable=False
    )

    # ==================================================
    # AUDIT TIMESTAMPS
    # ==================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # ==================================================
    # RELATIONSHIPS
    # ==================================================

    order = relationship(
        "Order",
        back_populates="items",
        passive_deletes=True,
    )

    variant = relationship(
        "ProductVariant",
        back_populates="order_items",
    )

    # ==================================================
    # INDEXES
    # ==================================================

    __table_args__ = (
        Index("idx_order_item_order", "order_id"),
        Index("idx_order_item_variant", "variant_id"),
    )