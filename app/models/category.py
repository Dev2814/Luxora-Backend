"""
Category Model

Represents hierarchical product categories.

Supports category trees such as:

Electronics
   ├── Mobile Phones
   │      ├── Android
   │      └── iPhone
   └── Laptops

Features:
- Self-referencing hierarchy
- SEO support
- Soft delete
- Category sorting
- Product relationships
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Boolean,
    Text,
    Index
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Category(Base):

    __tablename__ = "categories"

    # ==================================================
    # PRIMARY KEY
    # ==================================================

    id = Column(Integer, primary_key=True, index=True)

    # ==================================================
    # CATEGORY CORE DATA
    # ==================================================

    name = Column(
        String(255),
        nullable=False,
        index=True
    )

    slug = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    description = Column(
        Text,
        nullable=True
    )

    # ==================================================
    # CATEGORY TREE (HIERARCHY)
    # ==================================================

    parent_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # ==================================================
    # DISPLAY / STATUS
    # ==================================================

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # Used for ordering categories in UI
    sort_order = Column(
        Integer,
        default=0,
        nullable=False
    )

    # Soft delete support
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    # ==================================================
    # SEO SUPPORT
    # ==================================================

    meta_title = Column(
        String(255),
        nullable=True
    )

    meta_description = Column(
        String(500),
        nullable=True
    )

    # ==================================================
    # AUDIT TIMESTAMPS
    # ==================================================

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

    # ==================================================
    # RELATIONSHIPS
    # ==================================================

    # Parent category
    parent = relationship(
        "Category",
        remote_side=[id],
        back_populates="children"
    )

    # Child categories
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete"
    )

    # Products under this category
    products = relationship(
        "Product",
        back_populates="category",
        passive_deletes=True
    )

    # ==================================================
    # DATABASE INDEXES
    # ==================================================

    __table_args__ = (

        # Parent category lookup
        Index("idx_category_parent", "parent_id"),

        # Active category filtering
        Index("idx_category_active", "is_active"),

        # Category sorting
        Index("idx_category_sort", "sort_order"),
    )