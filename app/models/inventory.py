"""
Inventory Model

Tracks stock levels for each product variant.

Responsibilities:
- Maintain available stock
- Track reserved stock for pending orders
- Prevent overselling
- Provide low stock alerts
- Support optimistic locking
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Index,
    CheckConstraint
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Inventory(Base):
    """
    Inventory record for a product variant.

    Each variant has exactly ONE inventory record.
    """

    __tablename__ = "inventories"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(Integer, primary_key=True, index=True)

    # =========================================================
    # VARIANT RELATIONSHIP
    # =========================================================

    variant_id = Column(
        Integer,
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # =========================================================
    # STOCK MANAGEMENT
    # =========================================================

    stock = Column(
        Integer,
        nullable=False,
        default=0
    )

    reserved_stock = Column(
        Integer,
        nullable=False,
        default=0
    )

    low_stock_threshold = Column(
        Integer,
        nullable=False,
        default=5
    )

    # =========================================================
    # CONCURRENCY CONTROL
    # =========================================================

    version = Column(
        Integer,
        nullable=False,
        default=1,
        index=True
    )

    # =========================================================
    # AUDIT TIMESTAMPS
    # =========================================================

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

    # =========================================================
    # RELATIONSHIPS
    # =========================================================

    variant = relationship(
        "ProductVariant",
        back_populates="inventory",
        uselist=False
    )

    # =========================================================
    # HELPER PROPERTIES
    # =========================================================

    @property
    def available_stock(self) -> int:
        """
        Calculate available stock.
        """
        return max(self.stock - self.reserved_stock, 0)

    @property
    def is_low_stock(self) -> bool:
        """
        Check if stock is below threshold.
        """
        return self.available_stock <= self.low_stock_threshold

    # =========================================================
    # HELPER METHODS
    # =========================================================

    def increase_stock(self, quantity: int):
        """
        Add stock to inventory.
        """
        self.stock += quantity

    def decrease_stock(self, quantity: int):
        """
        Remove stock from inventory.
        """
        if quantity > self.available_stock:
            raise ValueError("Insufficient stock")

        self.stock -= quantity

    # =========================================================
    # DATABASE CONSTRAINTS
    # =========================================================

    __table_args__ = (

        CheckConstraint(
            "stock >= 0",
            name="check_inventory_stock_positive"
        ),

        CheckConstraint(
            "reserved_stock >= 0",
            name="check_inventory_reserved_positive"
        ),

        CheckConstraint(
            "reserved_stock <= stock",
            name="check_reserved_less_than_stock"
        ),

        Index("idx_inventory_variant", "variant_id"),
        Index("idx_inventory_low_stock", "low_stock_threshold"),
    )