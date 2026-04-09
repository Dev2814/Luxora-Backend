"""
Payment Repository
==================

Handles database operations related to payments.

Responsibilities
----------------
• Create payment record
• Retrieve payment by order
• Retrieve payment by transaction id
• Update payment status

Architecture
------------
Routes → Service → Repository → Database
"""

from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.payment import Payment



class PaymentRepository:
    """
    Repository responsible for payment database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    # CREATE PAYMENT
    # ======================================================

    def create(self, payment: Payment) -> Payment:
        """
        Create a new payment record.
        """

        self.db.add(payment)
        self.db.flush()

        return payment

    # ======================================================
    # GET PAYMENT BY ORDER
    # ======================================================

    def get_by_order_id(self, order_id: int) -> Optional[Payment]:
        """
        Retrieve payment associated with an order.
        """

        stmt = select(Payment).where(Payment.order_id == order_id)

        # return self.db.execute(stmt).scalar_one_or_none()
        return self.db.execute(stmt).scalars().first()

    # ======================================================
    # GET PAYMENT BY TRANSACTION
    # ======================================================

    def get_by_payment_intent(self, payment_intent: str) -> Optional[Payment]:
        """
        Retrieve payment by Stripe transaction id.
        """

        stmt = select(Payment).where(
            Payment.stripe_payment_intent == payment_intent
        )
        return self.db.execute(stmt).scalars().first()

    # ======================================================
    # UPDATE PAYMENT STATUS
    # ======================================================

    def update_status(self, payment: Payment, status):

        payment.status = status

        self.db.flush()

        return payment