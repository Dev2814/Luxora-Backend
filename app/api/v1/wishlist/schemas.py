"""
Wishlist Schemas
================

Enterprise-grade response schemas for wishlist.

Design Goals
------------
• Frontend-ready response (NO extra API calls needed)
• Includes product metadata
• Clean and scalable structure
• Pagination-ready
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# ======================================================
# ADD REQUEST
# ======================================================

class WishlistAddRequest(BaseModel):
    """
    Request schema for adding item to wishlist.
    """
    variant_id: int = Field(..., example=5)


# ======================================================
# ITEM RESPONSE (ENRICHED)
# ======================================================

class VariantAttributeResponse(BaseModel):
    attribute: str
    value: str

class WishlistItemResponse(BaseModel):
    """
    Represents a single wishlist item with enriched product data.
    """

    id: int
    variant_id: int
    product_id: int

    # Product Info
    product_name: str
    price: float
    compare_price: Optional[float] = None
    image: Optional[str]

    attributes: List[VariantAttributeResponse] = []
    
    # Inventory
    is_in_stock: bool

    # Timestamp
    created_at: datetime

    class Config:
        from_attributes = True


# ======================================================
# FULL RESPONSE
# ======================================================

class WishlistResponse(BaseModel):
    """
    Full wishlist response.

    Designed for scalability (pagination-ready).
    """

    items: List[WishlistItemResponse]
    total_items: int


# ======================================================
# GENERIC MESSAGE RESPONSE
# ======================================================

class MessageResponse(BaseModel):
    """
    Generic API message response.
    """

    message: str