"""
Review Schemas
==============

Defines request and response schemas for review APIs.

Design Goals
------------
• Clean API contract
• Frontend-ready responses (Amazon-style)
• Includes user info
• Includes analytics (summary + breakdown)
• Scalable structure

Architecture
------------
Client → Routes → Schemas → Service
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict

# ======================================================
# CREATE REVIEW REQUEST
# ======================================================

class ReviewCreateRequest(BaseModel):
    """
    Request schema for creating a review.
    """

    product_id: int
    variant_id: int

    rating: int = Field(..., ge=1, le=5)

    title: str
    comment: Optional[str] = None


# ======================================================
# HELPFUL VOTE REQUEST
# ======================================================

class ReviewVoteRequest(BaseModel):
    """
    Vote helpful / not helpful.
    """

    is_helpful: bool


# ======================================================
# REVIEW ITEM RESPONSE (FULLY ENRICHED)
# ======================================================

class ReviewItemResponse(BaseModel):
    """
    Represents a single review item.

    Includes:
    • User info
    • Review content
    • Verified badge
    • Helpful count
    """

    id: int
    user_id: int

    user_name: str
    user_email: str

    rating: int
    title: str
    comment: Optional[str]

    # 🔥 NEW (ADVANCED)
    is_verified: bool
    helpful_count: int

    created_at: datetime

    class Config:
        from_attributes = True


# ======================================================
# RATING SUMMARY
# ======================================================

class RatingSummaryResponse(BaseModel):
    """
    Aggregated rating data.
    """

    avg_rating: float
    total_reviews: int


# ======================================================
# REVIEW LIST RESPONSE (AMAZON STYLE)
# ======================================================

class ReviewListResponse(BaseModel):
    """
    Full review response.

    Includes:
    • Items
    • Total count
    • Rating summary
    • Rating breakdown
    """

    items: List[ReviewItemResponse]
    total_reviews: int

    # 🔥 NEW
    rating_summary: RatingSummaryResponse
    rating_breakdown: Dict[int, int]


# ======================================================
# GENERIC MESSAGE RESPONSE
# ======================================================

class MessageResponse(BaseModel):
    """
    Standard message response.
    """

    message: str