"""
Cart Schemas
============

Pydantic schemas used for request validation and response
serialization for cart operations.

Responsibilities
----------------
• Validate cart item creation
• Validate quantity updates
• Format cart response

Architecture
------------
Client → API Schema → Service → Repository → Database
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List


# ======================================================
# ADD ITEM TO CART
# ======================================================

class CartItemCreate(BaseModel):
    """
    Request schema for adding an item to cart.
    """

    variant_id: int = Field(
        ...,
        description="Product variant ID"
    )

    quantity: int = Field(
        ...,
        gt=0,
        description="Quantity to add"
    )


# ======================================================
# UPDATE CART ITEM
# ======================================================

class CartItemUpdate(BaseModel):
    """
    Request schema for updating cart item quantity.
    """

    variant_id: int

    quantity: int = Field(
        ...,
        gt=0
    )


# ======================================================
# CART ITEM RESPONSE
# ======================================================

class VariantAttributeResponse(BaseModel):
    attribute: str
    value: str

class CartItemResponse(BaseModel):
    """
    Response schema for a cart item.
    """

    id: int
    cart_id: int
    variant_id: int
    quantity: int

    product_id: int
    product_name: str
    price: float
    compare_price: float | None = None
    image: str | None = None
    attributes: List[VariantAttributeResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ======================================================
# CART RESPONSE
# ======================================================

class CartResponse(BaseModel):
    """
    Response schema for full cart.
    """

    items: List[CartItemResponse]