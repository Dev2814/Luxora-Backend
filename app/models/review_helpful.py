"""
Review Helpful Model
====================

Tracks helpful votes on reviews.

Purpose
-------
• Allow users to mark reviews as helpful
• Prevent duplicate votes per user
• Enable ranking of useful reviews

Architecture
------------
User → ReviewHelpful → Review

Design Goals
------------
• One vote per user per review
• Scalable for analytics
• Optimized for fast counting
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    Index
)

from sqlalchemy.orm import relationship

from app.models.base import Base


class ReviewHelpful(Base):
    """
    Represents a helpful vote on a review.
    """

    __tablename__ = "review_helpful"

    # ======================================================
    # PRIMARY KEY
    # ======================================================

    id = Column(Integer, primary_key=True, index=True)

    # ======================================================
    # RELATIONS
    # ======================================================

    review_id = Column(
        Integer,
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ======================================================
    # VOTE TYPE
    # ======================================================

    # True = helpful 👍
    # False = not helpful 👎 (optional future use)
    is_helpful = Column(
        Boolean,
        nullable=False
    )

    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    review = relationship(
        "Review",
        back_populates="helpful_votes"
    )

    user = relationship(
        "User"
    )

    # ======================================================
    # CONSTRAINTS & INDEXES
    # ======================================================

    __table_args__ = (

        # 🚫 Prevent duplicate votes by same user
        UniqueConstraint(
            "review_id",
            "user_id",
            name="uq_review_user_vote"
        ),

        # ⚡ Fast lookup for counting votes
        Index("idx_review_helpful_review", "review_id"),
    )