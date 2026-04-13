"""
Order Schemas
=============

Pydantic schemas used for request validation and response
serialization for order operations.

Responsibilities
----------------
• Validate checkout request
• Format order response
• Format order items response

Architecture
------------
Client → API Schema → Service → Repository → Database
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List
from decimal import Decimal


# ======================================================
# CART -> CHECKOUT REQUEST
# ======================================================

class CheckoutRequest(BaseModel):
    """
    Request schema used during checkout.
    """

    address_id: int = Field(
        ...,
        description="Shipping address ID"
    )

# ======================================================
# PRODUCT -> CHECKOUT REQUEST
# ======================================================

class BuyNowRequest(BaseModel):
    variant_id: int
    quantity: int
    address_id: int

# ======================================================
# ORDER ITEM RESPONSE
# ======================================================

class VariantAttributeResponse(BaseModel):
    attribute: str
    value: str

class OrderItemResponse(BaseModel):
    """
    Response schema for items inside an order.
    """

    id: int
    order_id: int
    variant_id: int
    quantity: int
    price_snapshot: Decimal
    subtotal: Decimal

    product_id: int
    product_name: str
    compare_price: Decimal | None = None
    image: str | None = None
    attributes: List[VariantAttributeResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ======================================================
# ORDER RESPONSE
# ======================================================

class OrderResponse(BaseModel):
    """
    Response schema for order details.
    """

    id: int
    user_id: int
    address_id: int
    status: str 
    payment_status: str
    total_amount: Decimal

    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


# ======================================================
# ORDER LIST RESPONSE
# ======================================================

class OrderListResponse(BaseModel):
    """
    Response schema for listing user orders.
    """

    orders: List[OrderResponse]

# =========================================================
# VENDOR ORDER DETAILS RESPONSE
# =========================================================

class VendorOrderItem(BaseModel):
    product_name: str
    variant_name: str
    quantity: int
    price: float
    subtotal: float


class VendorCustomerInfo(BaseModel):
    name: str
    email: str


class VendorOrderDetailsResponse(BaseModel):
    order_id: int
    status: str
    payment_status: str
    total_amount: float
    created_at: str

    customer: VendorCustomerInfo
    items: List[VendorOrderItem]


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

class UpdateOrderStatusRequest(BaseModel):
    status: str

# ======================================================
# VENDOR ORDER LIST RESPONSE
# ======================================================

class VendorOrderListItem(BaseModel):
    order_id: int
    customer_name: str
    total_amount: float
    status: str
    payment_status: str
    created_at: str


class VendorOrderListResponse(BaseModel):
    items: List[VendorOrderListItem]