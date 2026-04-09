"""
Product Image Model

Stores images associated with a product.

Features:
- Multiple images per product
- Primary image support
- Ordered gallery display
- Soft delete support
- CDN / storage compatible

Architecture:

Product
   └── ProductImage
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ProductImage(Base):
    """
    Represents an image belonging to a product.

    Example:

        Product: Nike Shoes

        Images:
            1 → thumbnail (primary)
            2 → side view
            3 → back view
    """

    __tablename__ = "product_images"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(Integer, primary_key=True, index=True)

    # =========================================================
    # PRODUCT RELATION
    # =========================================================

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # =========================================================
    # IMAGE DATA
    # =========================================================

    # CDN / storage URL
    image_url = Column(
        String(500),
        nullable=False
    )

    # Optional alt text (SEO + accessibility)
    alt_text = Column(
        String(255),
        nullable=True
    )

    # =========================================================
    # DISPLAY SETTINGS
    # =========================================================

    # Indicates thumbnail image
    is_primary = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    # Gallery order
    sort_order = Column(
        Integer,
        default=0,
        nullable=False
    )

    # =========================================================
    # STATUS FLAGS
    # =========================================================

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

    product = relationship(
        "Product",
        back_populates="images"
    )

    # =========================================================
    # DATABASE INDEXES
    # =========================================================

    __table_args__ = (

        # Fast lookup of images per product
        Index("idx_product_image_product", "product_id"),

        # Quickly fetch thumbnail
        Index("idx_product_image_primary", "is_primary"),

        # Gallery ordering
        Index("idx_product_image_sort", "sort_order"),

        # Prevent duplicate image ordering per product
        UniqueConstraint(
            "product_id",
            "sort_order",
            name="uq_product_image_sort"
        ),
    )