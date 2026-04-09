"""
Review Routes
=============

API endpoints for review system.

Features
--------
• Authenticated access (verified user)
• Clean response structure
• RESTful design
• Production-grade error handling
• Consistent with service & schemas

Architecture
------------
Client → Routes → Service → Repository → DB
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user

from app.domains.reviews.service import ReviewService
from app.api.v1.reviews.schemas import (
    ReviewCreateRequest,
    ReviewListResponse,
    RatingSummaryResponse,
    ReviewVoteRequest,
    MessageResponse
)

from app.core.logger import log_event


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)

# ======================================================
# DEPENDENCY
# ======================================================

def get_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db)

# ======================================================
# CREATE REVIEW
# ======================================================

@router.post(
    "/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review"
)
def create_review(
    payload: ReviewCreateRequest,
    service: ReviewService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Create a new review.

    Rules:
    • User must be authenticated
    • Must be a verified buyer
    • One review per product
    """

    try:

        return service.create_review(
            user_id=current_user["user_id"],
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            rating=payload.rating,
            title=payload.title,        # 🔥 FIXED
            comment=payload.comment
        )

    except ValueError as e:

        log_event(
            "review_create_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "review_create_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review"
        )

# ======================================================
# GET PRODUCT REVIEWS
# ======================================================

@router.get(
    "/product/{product_id}",
    response_model=ReviewListResponse,
    summary="Get product reviews"
)
def get_product_reviews(
    product_id: int,
    service: ReviewService = Depends(get_service)
):
    """
    Retrieve all reviews for a product.

    Returns:
    • List of reviews
    • Total review count
    """

    try:

        return service.get_product_reviews(product_id)

    except ValueError as e:

        log_event(
            "review_fetch_validation_error",
            level="warning",
            product_id=product_id,
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "review_fetch_server_error",
            level="critical",
            product_id=product_id,
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reviews"
        )

# ======================================================
# GET RATING SUMMARY
# ======================================================

@router.get(
    "/product/{product_id}/summary",
    response_model=RatingSummaryResponse,
    summary="Get product rating summary"
)
def get_rating_summary(
    product_id: int,
    service: ReviewService = Depends(get_service)
):
    """
    Get aggregated rating data.

    Returns:
    • Average rating
    • Total number of reviews
    """

    try:

        return service.get_rating_summary(product_id)

    except ValueError as e:

        log_event(
            "review_summary_validation_error",
            level="warning",
            product_id=product_id,
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "review_summary_server_error",
            level="critical",
            product_id=product_id,
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch rating summary"
        )
    
# ======================================================
# VOTE HELPFUL
# ======================================================

@router.post(
    "/{review_id}/helpful",
    response_model=MessageResponse,
    summary="Mark review as helpful / not helpful"
)
def vote_review_helpful(
    review_id: int,
    payload: ReviewVoteRequest,
    service: ReviewService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Mark a review as helpful.

    Rules:
    • One vote per user
    • Can update vote
    """

    try:

        return service.vote_review_helpful(
            user_id=current_user["user_id"],
            review_id=review_id,
            is_helpful=payload.is_helpful
        )

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "review_vote_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record vote"
        )