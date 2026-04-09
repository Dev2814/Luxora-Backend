"""
Product Model

Represents a product created by a vendor on the marketplace.

Architecture:
Vendor → Product → Variants → Inventory

Design goals:
- Support marketplace vendors
- Support product variants (size, color, storage etc.)
- Support SEO metadata
- Allow soft deletionF
- Enable efficient product search & filtering
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    DateTime,
    Numeric,
    Index
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Product(Base):
    """
    Product entity representing a sellable catalog item.

    One product can have:
    - multiple variants
    - multiple images
    - optional brand
    - optional category
    """

    __tablename__ = "products"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(Integer, primary_key=True, index=True)

    # =========================================================
    # FOREIGN KEYS
    # =========================================================

    # Vendor who owns the product
    vendor_id = Column(
        Integer,
        ForeignKey("vendor_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Optional brand association
    brand_id = Column(
        Integer,
        ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Product category
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # =========================================================
    # CORE PRODUCT DATA
    # =========================================================

    # Product display name
    name = Column(
        String(255),
        nullable=False,
        index=True
    )

    # SEO friendly slug (unique)
    slug = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    # Full product description
    description = Column(
        Text,
        nullable=True
    )

    # =========================================================
    # PRICING
    # =========================================================

    # Current selling price
    price = Column(
        Numeric(10, 2),
        nullable=False
    )

    # Original price (used for discount display)
    compare_price = Column(
        Numeric(10, 2),
        nullable=True
    )

    # Vendor internal cost (optional)
    cost_price = Column(
        Numeric(10, 2),
        nullable=True
    )

    # =========================================================
    # PRODUCT STATUS
    # =========================================================

    # Product visibility
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
    # SEO METADATA
    # =========================================================

    meta_title = Column(
        String(255),
        nullable=True
    )

    meta_description = Column(
        String(500),
        nullable=True
    )

    # =========================================================
    # AUDIT TIMESTAMPS
    # =========================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
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

    # Vendor relationship
    vendor = relationship(
        "VendorProfile",
        back_populates="products"
    )

    # Brand relationship
    brand = relationship(
        "Brand",
        lazy="joined"
    )

    # Category relationship
    category = relationship(
        "Category",
        back_populates="products",
        lazy="joined"
    )

    # Product images
    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        order_by="ProductImage.sort_order",
    )

    # Product variants
    variants = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )

    reviews = relationship(
        "Review",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


    # =========================================================
    # DATABASE INDEXES
    # =========================================================

    __table_args__ = (

        # Vendor product lookup
        Index("idx_product_vendor", "vendor_id"),

        # Category filtering
        Index("idx_product_category", "category_id"),

        # Active products filtering
        Index("idx_product_active", "is_active"),

        # Product search
        Index("idx_product_name", "name"),
    )