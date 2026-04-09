"""
Inventory Schemas
=================

Pydantic schemas used for request validation and response
serialization for inventory APIs.

Responsibilities
----------------
• Validate inventory creation requests
• Validate stock adjustment requests
• Standardize API responses
• Provide type safety between API and service layer

Architecture
------------
Client → API Schema → Service → Repository → Database
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


# =========================================================
# INVENTORY CREATE
# =========================================================

class InventoryCreate(BaseModel):
    """
    Schema used when admin creates inventory
    for a product variant.
    """

    variant_id: int = Field(
        ...,
        gt=0,
        description="Product variant ID"
    )

    stock: int = Field(
        default=0,
        ge=0,
        description="Initial stock quantity"
    )

    low_stock_threshold: int = Field(
        default=5,
        ge=0,
        description="Low stock alert threshold"
    )


# =========================================================
# INVENTORY UPDATE
# =========================================================

class InventoryUpdate(BaseModel):
    """
    Schema used for updating inventory values.
    """

    stock: Optional[int] = Field(
        None,
        ge=0,
        description="Updated stock value"
    )

    reserved_stock: Optional[int] = Field(
        None,
        ge=0,
        description="Reserved stock amount"
    )

    low_stock_threshold: Optional[int] = Field(
        None,
        ge=0,
        description="Low stock alert threshold"
    )


# =========================================================
# STOCK ADJUSTMENT
# =========================================================

class StockAdjustment(BaseModel):
    """
    Used for increase / decrease / reserve operations.
    """

    quantity: int = Field(
        ...,
        gt=0,
        description="Quantity to adjust"
    )


# =========================================================
# INVENTORY RESPONSE
# =========================================================

class ProductInfo(BaseModel):
    id: int
    name: str
    primary_image: Optional[str]


class VariantInfo(BaseModel):
    name: str
    sku: str
    price: float

class InventoryResponse(BaseModel):
    """
    Standard response returned for inventory APIs.
    """

    id: int
    variant_id: int

    product: ProductInfo
    variant: VariantInfo

    stock: int
    reserved_stock: int
    available_stock: int
    low_stock_threshold: int

    is_low_stock: bool

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# INVENTORY LIST RESPONSE
# =========================================================

class InventoryListResponse(BaseModel):
    """
    Paginated inventory list response used by admin dashboards.
    """

    total: int
    page: int
    limit: int
    low_stock_count: int
    items: List[InventoryResponse]