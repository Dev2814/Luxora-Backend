"""
Stripe Webhook Handler
======================

Handles incoming webhook events from Stripe.

Responsibilities
----------------
• Verify Stripe webhook signature
• Detect payment success
• Detect payment failure
• Call payment service
"""

import stripe
from fastapi import Request, HTTPException

from app.core.config import settings
from app.infrastructure.database.session import SessionLocal
from app.domains.payments.service import PaymentService


stripe.api_key = settings.STRIPE_SECRET_KEY


async def handle_stripe_webhook(request: Request):

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )

    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    db = SessionLocal()

    try:
        payment_service = PaymentService(db)

        # ---------------------------------------------------
        # PAYMENT SUCCESS
        # ---------------------------------------------------

        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            payment_intent_id = payment_intent["id"]

            payment_service.handle_payment_success(payment_intent_id)

        # ---------------------------------------------------
        # PAYMENT FAILED
        # ---------------------------------------------------

        elif event["type"] == "payment_intent.payment_failed":

            payment_intent = event["data"]["object"]

            payment_service.handle_payment_failed(payment_intent["id"])

        return {"status": "success"}

    finally:
        db.close()


# stripe listen --forward-to localhost:8000/api/v1/payments/webhook
# stripe listen --forward-to localhost:2814/api/v1/payments/webhook