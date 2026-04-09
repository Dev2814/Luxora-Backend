"""
Product Variant Model

Represents a purchasable variation of a product.

Examples:

T-Shirt
 ├── Size S
 ├── Size M
 └── Size L

iPhone
 ├── 128GB
 ├── 256GB
 └── 512GB

Architecture:
Product → Variant → Inventory

Design goals:
- Support product variations (size, color, storage)
- Maintain unique SKU for logistics
- Allow attribute mapping (Color, Size etc.)
- Maintain independent inventory per variant
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Numeric,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ProductVariant(Base):
    """
    Represents a specific purchasable variation of a product.

    Example:
        Product: iPhone 15
        Variants:
            - Black 128GB
            - Black 256GB
            - Blue 128GB
    """

    __tablename__ = "product_variants"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(Integer, primary_key=True, index=True)

    # =========================================================
    # FOREIGN KEY
    # =========================================================

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # =========================================================
    # VARIANT INFORMATION
    # =========================================================

    # Example: "Black 128GB"
    name = Column(
        String(255),
        nullable=False
    )

    # SEO slug for variant (optional)
    slug = Column(
        String(255),
        nullable=True,
        index=True
    )

    # Unique SKU used by warehouse & logistics
    sku = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # =========================================================
    # PRICING
    # =========================================================

    # Variant specific price
    price = Column(
        Numeric(10, 2),
        nullable=False
    )

    # =========================================================
    # STATUS FLAGS
    # =========================================================

    # Variant visibility
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # Soft delete flag
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    # =========================================================
    # TIMESTAMPS
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

    # Parent product
    product = relationship(
        "Product",
        back_populates="variants"
    )

    # Order items that include this variant
    order_items = relationship(
        "OrderItem",
        back_populates="variant"
    )

    reviews = relationship(
        "Review",
        back_populates="variant"
    )

    # Inventory record (1 variant → 1 inventory)
    inventory = relationship(
        "Inventory",
        back_populates="variant",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Mapping table for attributes
    attribute_maps = relationship(
        "ProductAttributeMap",
        back_populates="variant",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Direct access to attribute values
    attribute_values = relationship(
        "ProductAttributeValue",
        secondary="product_attribute_map",
        lazy="joined",
        overlaps="attribute_maps,variant,attribute_value"
    )

    wishlist_items = relationship(
        "WishlistItem",
        back_populates="variant",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # =========================================================
    # DATABASE INDEXES
    # =========================================================

    __table_args__ = (

        # Fast lookup of variants for a product
        Index("idx_variant_product", "product_id"),

        # SKU search (logistics, inventory systems)
        Index("idx_variant_sku", "sku"),

        # Filter active variants
        Index("idx_variant_active", "is_active"),

        # Prevent duplicate variant names per product
        UniqueConstraint(
            "product_id",
            "name",
            name="uq_variant_product_name"
        ),
    )