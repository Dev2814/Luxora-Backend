"""
Payment Routes
==============

API endpoints for payment operations.

Responsibilities
----------------
• Create Stripe payment intent
• Receive Stripe webhook events
• Check payment status

Architecture
------------
Routes → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.domains.payments.service import PaymentService
from app.domains.payments.repository import PaymentRepository
from app.webhooks.stripe_webhook import handle_stripe_webhook

from app.api.v1.payments.schemas import (
    CreatePaymentRequest,
    PaymentResponse,
    PaymentStatusResponse
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


# ======================================================
# CREATE PAYMENT
# ======================================================

@router.post(
    "/create",
    response_model=PaymentResponse,
    summary="Create Stripe Payment"
)
def create_payment(
    payload: CreatePaymentRequest,
    db: Session = Depends(get_db)
):

    service = PaymentService(db)

    try:

        return service.create_payment_intent(payload.order_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ======================================================
# STRIPE WEBHOOK
# ======================================================

@router.post(
    "/webhook",
    summary="Stripe Webhook Handler"
)
async def stripe_webhook(request: Request):

    return await handle_stripe_webhook(request)


# ======================================================
# GET PAYMENT STATUS
# ======================================================

@router.get(
    "/status/{order_id}",
    response_model=PaymentStatusResponse,
    summary="Get Payment Status"
)
def get_payment_status(
    order_id: int,
    db: Session = Depends(get_db)
):

    repo = PaymentRepository(db)

    payment = repo.get_by_order_id(order_id)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "order_id": payment.order_id,
        "payment_status": payment.status,
        "amount": payment.amount
    }


