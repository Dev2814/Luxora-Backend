"""
Coupon Schemas
==============

Defines request and response schemas for coupon system.

Design Goals
------------
• Frontend-ready responses
• Clean API contract
• Supports checkout flow
• Validation at API layer
• Scalable structure

Architecture
------------
Client → Routes → Schemas → Service
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ======================================================
# CREATE COUPON (ADMIN)
# ======================================================

class CouponCreateRequest(BaseModel):
    """
    Admin coupon creation schema.

    Used for:
    • Admin panel
    • Marketing campaigns
    """

    code: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None

    # Coupon type: percentage / flat
    type: str = Field(..., pattern="^(percentage|flat)$")

    # Discount value
    value: float = Field(..., gt=0)

    # Optional constraints
    max_discount: Optional[float] = Field(default=None, ge=0)
    min_order_amount: Optional[float] = Field(default=None, ge=0)

    # Usage limits
    usage_limit: Optional[int] = Field(default=None, ge=1)
    usage_per_user: Optional[int] = Field(default=None, ge=1)

    # Validity
    valid_from: datetime
    valid_until: datetime


# ======================================================
# APPLY COUPON REQUEST
# ======================================================

class ApplyCouponRequest(BaseModel):
    """
    Request to apply coupon before checkout.
    """

    code: str = Field(..., min_length=3, max_length=50)
    order_amount: float = Field(..., gt=0)


# ======================================================
# APPLY COUPON RESPONSE
# ======================================================

class ApplyCouponResponse(BaseModel):
    """
    Response after applying coupon.

    Used in:
    • Cart page
    • Checkout summary
    """

    coupon_id: int
    code: str

    discount: float
    final_amount: float


# ======================================================
# VALIDATE COUPON RESPONSE (OPTIONAL LIGHTWEIGHT)
# ======================================================

class ValidateCouponResponse(BaseModel):
    """
    Lightweight validation response.

    Useful for:
    • Instant UI validation
    """

    is_valid: bool
    message: str


# ======================================================
# GENERIC MESSAGE RESPONSE
# ======================================================

class MessageResponse(BaseModel):
    """
    Standard API message response.
    """

    message: str