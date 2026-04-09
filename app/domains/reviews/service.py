"""
Review Service
==============

Handles business logic for reviews.

Responsibilities
----------------
• Validate purchase (verified buyer)
• Prevent duplicate reviews
• Create review
• Fetch product reviews (with user info + helpful votes)
• Return rating summary + breakdown
• Handle helpful votes

Architecture
------------
Routes → Service → Repository → DB
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.review import Review
from app.models.product_variant import ProductVariant

from app.domains.reviews.repository import ReviewRepository
from app.core.logger import log_event


class ReviewService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReviewRepository(db)

    # ======================================================
    # CREATE REVIEW
    # ======================================================

    def create_review(
        self,
        user_id: int,
        product_id: int,
        variant_id: int,
        rating: int,
        title: str,
        comment: str | None
    ):

        try:

            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")

            variant = self.db.get(ProductVariant, variant_id)

            if not variant:
                raise ValueError("Product variant not found")

            if not self.repo.has_purchased_product(user_id, variant_id):
                raise ValueError("Only verified buyers can review")

            existing = self.repo.get_by_user_product(user_id, product_id)

            if existing:
                raise ValueError("You already reviewed this product")

            review = Review(
                user_id=user_id,
                product_id=product_id,
                variant_id=variant_id,
                rating=rating,
                title=title,
                comment=comment,
                is_verified=True  # 🔥 important
            )

            self.repo.create(review)
            self.db.commit()

            log_event(
                "review_created",
                user_id=user_id,
                product_id=product_id,
                rating=rating
            )

            return {"message": "Review submitted successfully"}

        except ValueError:
            raise

        except SQLAlchemyError as e:
            self.db.rollback()

            log_event(
                "review_create_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to submit review")

    # ======================================================
    # GET PRODUCT REVIEWS (AMAZON STYLE)
    # ======================================================

    def get_product_reviews(self, product_id: int):
        """
        Full enriched response:
        • reviews
        • helpful_count
        • rating summary
        • rating breakdown
        """

        try:

            reviews = self.repo.get_product_reviews(product_id)

            items = []

            for review in reviews:

                user = review.user

                helpful_count = self.repo.get_helpful_count(review.id)

                items.append({
                    "id": review.id,
                    "user_id": review.user_id,

                    "user_name": (
                        getattr(user.customer_profile, "full_name", None)
                        or getattr(user, "name", None)
                        or f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
                        or ""
                    ) if user else "",

                    "user_email": getattr(user, "email", "") if user else "",

                    "rating": review.rating,
                    "title": review.title,
                    "comment": review.comment,

                    "is_verified": review.is_verified,  # 🔥 NEW
                    "helpful_count": helpful_count,     # 🔥 NEW

                    "created_at": review.created_at
                })

            # 🔥 AGGREGATES
            summary = self.repo.get_product_rating_summary(product_id)
            breakdown = self.repo.get_rating_breakdown(product_id)

            return {
                "items": items,
                "total_reviews": len(items),
                "rating_summary": summary,
                "rating_breakdown": breakdown
            }

        except Exception as e:

            log_event(
                "review_fetch_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to fetch reviews")

    # ======================================================
    # HELPFUL VOTE
    # ======================================================

    def vote_review_helpful(
        self,
        user_id: int,
        review_id: int,
        is_helpful: bool
    ):
        """
        Add/update helpful vote.
        """

        try:

            self.repo.add_helpful_vote(
                user_id=user_id,
                review_id=review_id,
                is_helpful=is_helpful
            )

            self.db.commit()

            return {"message": "Vote recorded"}

        except Exception as e:

            self.db.rollback()

            log_event(
                "review_vote_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to record vote")

    # ======================================================
    # GET SUMMARY ONLY
    # ======================================================

    def get_rating_summary(self, product_id: int):

        try:
            return self.repo.get_product_rating_summary(product_id)

        except Exception as e:

            log_event(
                "review_summary_error",
                level="error",
                error=str(e)
            )

            raise ValueError("Unable to fetch rating summary")

    # ======================================================
    # GET BREAKDOWN ONLY
    # ======================================================

    def get_rating_breakdown(self, product_id: int):

        return self.repo.get_rating_breakdown(product_id)