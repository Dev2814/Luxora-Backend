"""
Brand Model (Enterprise + SEO Ready)
===================================

Represents a product brand in the marketplace.

Design Goals
------------
• SEO optimized (slug + meta)
• Soft delete support
• Scalable for large catalog
• Fast filtering & indexing

Examples:
    Nike
    Apple
    Adidas
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Brand(Base):

    __tablename__ = "brands"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(Integer, primary_key=True, index=True)

    # =========================================================
    # CORE DATA
    # =========================================================

    name = Column(
        String(200),
        nullable=False,
        unique=True,
        index=True
    )

    logo = Column(
        String(500),
        nullable=True
    )

    # SEO-friendly unique slug
    slug = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    # =========================================================
    # SEO FIELDS
    # =========================================================

    meta_title = Column(String(255), nullable=True)

    meta_description = Column(String(500), nullable=True)

    # =========================================================
    # STATUS FLAGS
    # =========================================================

    is_active = Column(Boolean, default=True, nullable=False, index=True)

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    # =========================================================
    # TIMESTAMPS
    # =========================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # =========================================================
    # RELATIONSHIPS
    # =========================================================

    products = relationship(
        "Product",
        back_populates="brand",
        passive_deletes=True
    )

    # =========================================================
    # INDEXES (Performance Optimization)
    # =========================================================

    __table_args__ = (
        Index("idx_brand_slug", "slug"),
        Index("idx_brand_active", "is_active"),
    )