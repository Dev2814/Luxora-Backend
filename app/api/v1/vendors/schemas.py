"""
Vendor Schemas

Defines request and response models used by vendor APIs.

Responsibilities:
- Vendor onboarding (apply)
- Vendor profile responses
- Vendor updates
- Vendor product listings

These schemas are used by:

Routes → Service → Repository → Database
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.vendor_profile import VendorStatus


# ======================================================
# VENDOR APPLY
# ======================================================

class VendorApply(BaseModel):
    """
    Vendor application request.

    Used when a user applies to become a vendor.
    """

    store_name: str = Field(..., min_length=2, max_length=255)

    business_name: str = Field(..., min_length=2, max_length=255)

    gst_number: Optional[str] = Field(default=None, max_length=50)

    business_address: str = Field(..., max_length=500)


# ======================================================
# VENDOR UPDATE
# ======================================================

class VendorUpdate(BaseModel):
    """
    Allows vendors to update their store profile.
    """

    store_name: Optional[str] = Field(None, min_length=2, max_length=255)

    store_description: Optional[str] = None

    store_logo: Optional[str] = None

    business_name: Optional[str] = None

    gst_number: Optional[str] = None

    business_address: Optional[str] = None


# ======================================================
# VENDOR RESPONSE
# ======================================================

class VendorProfileResponse(BaseModel):
    """
    Vendor profile response returned by APIs.
    """

    id: int
    user_id: int

    email: Optional[str] = None
    phone: Optional[str] = None


    store_name: str
    store_slug: Optional[str] = None

    store_logo: Optional[str]
    store_description: Optional[str]

    business_name: str
    gst_number: Optional[str]
    business_address: str

    verification_status: VendorStatus
    rejection_reason: Optional[str]

    commission_rate: float
    is_active: bool

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


from typing import List


# ======================================================
# VENDOR PRODUCT (ENTERPRISE LIST RESPONSE)
# ======================================================

class VendorProductImage(BaseModel):
    id: int
    image_url: str
    is_primary: bool
    sort_order: int


class VendorProductVariant(BaseModel):
    id: int
    name: str
    sku: str
    price: float


class VendorProductItem(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]

    price: float
    compare_price: Optional[float]

    brand_id: int
    category_id: int

    status: str

    primary_image: Optional[str]

    images: List[VendorProductImage]
    variants: List[VendorProductVariant]

    total_stock: int


class VendorProductListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[VendorProductItem]

# ======================================================
# ADMIN VENDOR APPROVAL
# ======================================================

class VendorApproval(BaseModel):
    """
    Used by admin to approve or reject vendors.
    """

    status: VendorStatus

    rejection_reason: Optional[str] = None