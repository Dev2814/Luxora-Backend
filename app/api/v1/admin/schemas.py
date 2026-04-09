"""
Admin Schemas

Defines request and response models for admin APIs.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


# --------------------------------------------------
# APPROVE VENDOR REQUEST
# --------------------------------------------------

class ApproveVendorRequest(BaseModel):

    vendor_id: int = Field(..., gt=0, description="Vendor ID to approve")


# --------------------------------------------------
# REJECT VENDOR REQUEST
# --------------------------------------------------

class RejectVendorRequest(BaseModel):

    reason: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Reason for vendor rejection"
    )


# --------------------------------------------------
# DEACTIVATE USER REQUEST
# --------------------------------------------------

class DeactivateUserRequest(BaseModel):

    user_id: int = Field(..., gt=0, description="User ID to deactivate")


# --------------------------------------------------
# BRAND CREATE REQUEST
# --------------------------------------------------

class BrandCreate(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Brand name"
    )

    logo: Optional[str] = Field(
        None,
        description="Brand logo URL"
    )


# --------------------------------------------------
# BRAND RESPONSE
# --------------------------------------------------

class BrandResponse(BaseModel):

    id: int
    name: str
    logo: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# BRAND LIST RESPONSE
# --------------------------------------------------

class BrandListResponse(BaseModel):

    brands: List[BrandResponse]


# --------------------------------------------------
# ADMIN ANALYTICS RESPONSE
# --------------------------------------------------

class AdminAnalyticsResponse(BaseModel):

    total_users: int
    total_vendors: int
    total_buyers:int
    approved_vendors: int
    pending_vendors: int


# --------------------------------------------------
# GENERIC MESSAGE RESPONSE
# --------------------------------------------------

class MessageResponse(BaseModel):

    message: str