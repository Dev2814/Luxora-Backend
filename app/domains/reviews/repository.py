"""
Review Repository
=================

Handles all database operations related to reviews.

Responsibilities
----------------
• Create review
• Fetch review by user & product (duplicate check)
• Fetch product reviews (with user info + filtering)
• Validate purchase (via order items)
• Aggregate rating data
• Handle helpful votes

Design Principles
-----------------
• NO business logic
• Pure DB layer
• Optimized queries (NO N+1)
• Scalable for analytics

Architecture
------------
Service → Repository → Database
"""

from typing import Optional, List

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from app.models.review import Review
from app.models.review_helpful import ReviewHelpful
from app.models.order_item import OrderItem
from app.models.order import Order


class ReviewRepository:
    """
    Repository layer for review operations.
    """

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # GET REVIEW (DUPLICATE CHECK)
    # ======================================================

    def get_by_user_product(
        self,
        user_id: int,
        product_id: int
    ) -> Optional[Review]:

        stmt = (
            select(Review)
            .where(
                Review.user_id == user_id,
                Review.product_id == product_id
            )
        )

        return self.db.execute(stmt).scalar_one_or_none()

    # ======================================================
    # CREATE REVIEW
    # ======================================================

    def create(self, review: Review) -> Review:

        self.db.add(review)
        self.db.flush()
        return review

    # ======================================================
    # VERIFY PURCHASE (VERIFIED BUYER)
    # ======================================================

    def has_purchased_product(
        self,
        user_id: int,
        variant_id: int
    ) -> bool:

        stmt = (
            select(OrderItem.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.user_id == user_id,
                OrderItem.variant_id == variant_id
            )
            .limit(1)
        )

        return self.db.execute(stmt).first() is not None

    # ======================================================
    # GET PRODUCT REVIEWS (OPTIMIZED + FILTERED)
    # ======================================================

    def get_product_reviews(
        self,
        product_id: int
    ) -> List[Review]:
        """
        Fetch approved reviews only.

        Performance:
        • joinedload → no N+1
        • filters moderation
        """

        stmt = (
            select(Review)
            .where(
                Review.product_id == product_id,
                Review.is_approved == True,   # 🔥 moderation filter
                Review.is_flagged == False
            )
            .order_by(Review.created_at.desc())
            .options(
                joinedload(Review.user)
            )
        )

        return self.db.execute(stmt).scalars().all()

    # ======================================================
    # GET RATING BREAKDOWN
    # ======================================================

    def get_rating_breakdown(self, product_id: int):

        stmt = (
            select(
                Review.rating,
                func.count(Review.id)
            )
            .where(
                Review.product_id == product_id,
                Review.is_approved == True
            )
            .group_by(Review.rating)
        )

        results = self.db.execute(stmt).all()

        breakdown = {i: 0 for i in range(1, 6)}

        for rating, count in results:
            breakdown[rating] = count

        return breakdown

    # ======================================================
    # GET RATING SUMMARY
    # ======================================================

    def get_product_rating_summary(
        self,
        product_id: int
    ):

        stmt = (
            select(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("total_reviews")
            )
            .where(
                Review.product_id == product_id,
                Review.is_approved == True
            )
        )

        result = self.db.execute(stmt).one()

        return {
            "avg_rating": float(result.avg_rating) if result.avg_rating else 0.0,
            "total_reviews": result.total_reviews
        }

    # ======================================================
    # ADD / UPDATE HELPFUL VOTE
    # ======================================================

    def add_helpful_vote(
        self,
        user_id: int,
        review_id: int,
        is_helpful: bool
    ) -> None:
        """
        Add or update helpful vote.

        • One user → one vote
        """

        # check existing vote
        stmt = (
            select(ReviewHelpful)
            .where(
                ReviewHelpful.user_id == user_id,
                ReviewHelpful.review_id == review_id
            )
        )

        existing = self.db.execute(stmt).scalar_one_or_none()

        if existing:
            existing.is_helpful = is_helpful
        else:
            vote = ReviewHelpful(
                user_id=user_id,
                review_id=review_id,
                is_helpful=is_helpful
            )
            self.db.add(vote)

        self.db.flush()

    # ======================================================
    # GET HELPFUL COUNT
    # ======================================================

    def get_helpful_count(self, review_id: int) -> int:
        """
        Count helpful votes (only positive).
        """

        stmt = (
            select(func.count(ReviewHelpful.id))
            .where(
                ReviewHelpful.review_id == review_id,
                ReviewHelpful.is_helpful == True
            )
        )

        return self.db.execute(stmt).scalar() or 0