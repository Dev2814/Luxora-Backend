"""
Customer Schemas
================

Pydantic schemas used for request validation and response
serialization for customer profile operations.

Responsibilities
----------------
• Validate customer profile creation
• Validate profile updates
• Standardize API responses
• Ensure type safety

Architecture
------------
Client → API Schema → Service → Repository → Database
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date

from app.models.customer_profile import Gender


# =========================================================
# CUSTOMER CREATE
# =========================================================

class CustomerCreate(BaseModel):
    """
    Schema used when creating a customer profile.
    """

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Customer full name"
    )

    gender: Optional[Gender] = Field(
        default=None,
        description="Customer gender"
    )

    date_of_birth: Optional[date] = Field(
        default=None,
        description="Customer date of birth"
    )


# =========================================================
# CUSTOMER UPDATE
# =========================================================

class CustomerUpdate(BaseModel):
    """
    Schema used for updating customer profile information.
    """

    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Customer full name"
    )

    gender: Optional[Gender] = Field(
        default=None,
        description="Customer gender"
    )

    date_of_birth: Optional[date] = Field(
        default=None,
        description="Customer date of birth"
    )


# =========================================================
# CUSTOMER RESPONSE
# =========================================================

class CustomerResponse(BaseModel):
    """
    Standard API response schema for customer profile.
    """

    id: int
    user_id: int

    full_name: str
    gender: Optional[Gender]
    date_of_birth: Optional[date]

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# CUSTOMER LIST RESPONSE
# =========================================================

class CustomerListResponse(BaseModel):
    """
    Paginated response used for admin customer listings.
    """

    total: int
    page: int
    limit: int

    items: list[CustomerResponse]