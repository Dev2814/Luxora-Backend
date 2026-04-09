"""
Product Schemas

Pydantic schemas used for request validation and response serialization.

Responsibilities:
- Product creation validation
- Product update validation
- Image upload response
- API response formatting

Architecture:
    Client → API Schema → Service → Database
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from decimal import Decimal


# ==================================================
# PRODUCT IMAGE
# ==================================================

class ProductImageCreate(BaseModel):
    """Used internally when creating images via URL (not file upload)."""
    image_url: str = Field(..., max_length=500)
    is_primary: bool = False
    sort_order: int = Field(default=0, ge=0)


class ProductImageResponse(BaseModel):
    id: int
    image_url: str
    is_primary: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


# ==================================================
# IMAGE UPLOAD RESPONSE
# Returned after POST /{product_id}/images
# ==================================================

class ProductImageUploadResponse(BaseModel):
    """
    Response returned after uploading images to a product.
    Shows how many were uploaded and the full updated image list.
    """
    product_id: int
    uploaded_count: int
    images: List[ProductImageResponse]


# ==================================================
# PRODUCT VARIANT
# ==================================================

class ProductVariantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    # sku: str = Field(..., min_length=3, max_length=100)
    price: Decimal = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    attribute_value_ids: List[int] = []

class VariantAttributeResponse(BaseModel):
    attribute: str
    value: str

class ProductVariantResponse(BaseModel):
    id: int 
    name: str
    sku: str
    price: Decimal
    attributes: List[VariantAttributeResponse] = []

    stock_status: str
    available_stock: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ==================================================
# PRODUCT CREATE
# NOTE: Images are NOT included here.
# Upload images separately via POST /{product_id}/images
# ==================================================

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    compare_price: Optional[Decimal] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    variants: List[ProductVariantCreate] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Nike Air Max",
                "description": "Premium running shoes",
                "price": 4999.00,
                "compare_price": 5999.00,
                "brand_id": 1,
                "category_id": 2,
                "variants": [
                    {
                        "name": "Size 8 Black",
                        "price": 4999.00,
                        "stock": 50,
                        "attribute_value_ids": [2, 4]
                    },
                    {
                        "name": "Size 9 White",
                        "price": 4999.00,
                        "stock": 30,
                        "attribute_value_ids": [3, 5]
                    }
                ]
            }
        }
    )


# ==================================================
# PRODUCT UPDATE
# ==================================================

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = None
    compare_price: Optional[Decimal] = None
    stock: Optional[int] = Field(None, ge=0)
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


# ==================================================
# PRODUCT RESPONSE
# ==================================================

class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    price: Decimal
    compare_price: Optional[Decimal]
    brand_id: Optional[int]
    category_id: Optional[int]
    is_active: bool
    images: List[ProductImageResponse] = Field(default_factory=list)
    variants: List[ProductVariantResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)





# ==================================================
# PAGINATED PRODUCT RESPONSE
# ==================================================

class ProductListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[ProductResponse]