"""
Review Model
============

Represents a user review for a product.

Design Goals
------------
• Product-level reviews with optional variant context
• Verified buyer support
• Prevent duplicate reviews
• Scalable for analytics (ratings, summaries)
• Supports moderation & helpful votes

Architecture
------------
User → Review → Product
                ↳ Variant (optional)
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Text,
    DateTime,
    Index,
    UniqueConstraint,
    CheckConstraint,
    Boolean,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Review(Base):
    """
    Represents a product review submitted by a user.
    """

    __tablename__ = "reviews"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(Integer, primary_key=True, index=True)

    # =========================================================
    # RELATIONS
    # =========================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Optional (variant-specific context)
    variant_id = Column(
        Integer,
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # =========================================================
    # REVIEW CONTENT
    # =========================================================

    rating = Column(Integer, nullable=False)

    title = Column(
        String(255),
        nullable=False
    )

    comment = Column(
        Text,
        nullable=True
    )

    # =========================================================
    # VERIFICATION & MODERATION
    # =========================================================

    # ✅ Verified purchase (important for trust)
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    # 🛑 Moderation system (enterprise feature)
    is_approved = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    is_flagged = Column(
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

    user = relationship(
        "User",
        back_populates="reviews"
    )

    product = relationship(
        "Product",
        back_populates="reviews"
    )

    variant = relationship(
        "ProductVariant",
        back_populates="reviews"
    )

    # 👍 Helpful votes
    helpful_votes = relationship(
        "ReviewHelpful",
        back_populates="review",
        cascade="all, delete-orphan"
    )

    # =========================================================
    # CONSTRAINTS
    # =========================================================

    __table_args__ = (

        # 🚫 Prevent duplicate review per user per product
        UniqueConstraint(
            "user_id",
            "product_id",
            name="uq_user_product_review"
        ),

        # ⭐ Rating must be between 1 and 5
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="check_rating_range"
        ),

        # ⚡ Performance indexes
        Index("idx_review_product", "product_id"),
        Index("idx_review_user", "user_id"),
        Index("idx_review_verified", "is_verified"),
    )