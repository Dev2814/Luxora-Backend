"""
Payment Schemas
===============

Pydantic schemas for payment APIs.

Responsibilities
----------------
• Validate payment creation request
• Format payment responses
"""

from pydantic import BaseModel, ConfigDict
from decimal import Decimal


# ======================================================
# CREATE PAYMENT REQUEST
# ======================================================

class CreatePaymentRequest(BaseModel):
    """
    Request schema for creating a payment.
    """

    order_id: int


# ======================================================
# PAYMENT RESPONSE
# ======================================================

class PaymentResponse(BaseModel):
    """
    Response schema for payment intent.
    """

    client_secret: str

    model_config = ConfigDict(from_attributes=True)


# ======================================================
# PAYMENT STATUS RESPONSE
# ======================================================

class PaymentStatusResponse(BaseModel):
    """
    Response schema for payment status.
    """

    order_id: int
    payment_status: str
    amount: Decimal