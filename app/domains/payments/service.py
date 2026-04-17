"""
Payment Service
===============

Handles Stripe payment processing and webhook events.

Responsibilities
----------------
• Create Stripe payment intent
• Store payment record
• Handle webhook events
• Update payment status
• Update order status
• Trigger invoice generation
"""

import stripe
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order, PaymentStatus as OrderPaymentStatus
from app.models.order import OrderStatus
from app.domains.payments.repository import PaymentRepository
from app.domains.orders.repository import OrderRepository

from app.infrastructure.invoice.service import InvoiceService
from app.core.logger import log_event


# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:

    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)
        self.invoice_service = InvoiceService(self.db)

    # ======================================================
    # CREATE PAYMENT INTENT
    # ======================================================

    def create_payment_intent(self, order_id: int):

        order = self.order_repo.get_order_by_id(order_id)

        if not order:
            raise ValueError("Order not found")

        amount = int(order.total_amount * 100)  # Stripe uses cents

        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            metadata={"order_id": order.id},
            automatic_payment_methods={"enabled": True}
        )

        payment = self.payment_repo.get_by_order_id(order.id)

        if not payment:
            payment = Payment(
                order_id=order.id,
                amount=order.total_amount,
                status=PaymentStatus.PENDING,
                stripe_payment_intent=intent.id
            )
            self.payment_repo.create(payment)
        else:
            payment.stripe_payment_intent = intent.id

        self.db.commit()
        self.db.refresh(payment)

        return {
            "client_secret": intent.client_secret
        }

    # ======================================================
    # HANDLE PAYMENT SUCCESS
    # ======================================================

    def handle_payment_success(self, payment_intent_id: str):

        payment = self.payment_repo.get_by_payment_intent(payment_intent_id)

        if not payment or payment.status == PaymentStatus.PAID:
            return

        payment.status = PaymentStatus.PAID
        payment.transaction_id = payment_intent_id

        order = payment.order
        order.payment_status = OrderPaymentStatus.PAID
        order.status = OrderStatus.CONFIRMED

        order.payment_method = "Stripe"

        self.db.commit()
        self.db.refresh(payment)

        if not order.address:
            log_event(
                "invoice_missing_address",
                level="warning",
                order_id=order.id
            )

        try:
            pdf_path = self.invoice_service.create_invoice(order.id)

            log_event(
                "invoice_generated_success",
                order_id=order.id,
                pdf_path=pdf_path
            )

        except Exception as e:
            log_event(
                "invoice_generation_failed",
                level="warning",
                order_id=order.id,
                error=str(e)
            )

    
    # ======================================================
    # HANDLE PAYMENT FAILED
    # ======================================================

    def handle_payment_failed(self, payment_intent_id: str):

        payment = self.payment_repo.get_by_payment_intent(payment_intent_id)

        if not payment:
            return

        payment.status = PaymentStatus.FAILED

        order = payment.order
        order.payment_status = OrderPaymentStatus.FAILED

        self.db.commit()
        self.db.refresh(payment)