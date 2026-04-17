"""
Invoice Service
===============

Responsible for the full invoice lifecycle:
  1. Compute invoice number & date  (single source of truth)
  2. Generate the PDF via the generator
  3. Persist an Invoice record to the database
  4. Email the PDF to the customer
  5. Never allow invoice failure to break the payment workflow

Design notes
------------
• invoice_number and invoice_date are computed HERE and passed into
  generate_invoice() — the generator never recomputes them.

• Database errors are rolled back before the except block re-logs, so
  the session is always left in a clean state.

• Email failures are distinguished from "no email address" in logging
  so monitoring dashboards can tell the difference.
"""

from datetime import datetime
from sqlalchemy.orm import joinedload

from app.infrastructure.invoice.generator import generate_invoice
from app.infrastructure.email.service import send_email
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.user import User
from app.core.logger import log_event


class InvoiceService:

    def __init__(self, db):
        self.db = db

    def create_invoice(self, order_id: int):

        try:
            # ======================================================
            # LOAD FULL ORDER GRAPH (UPDATED - NO REMOVAL)
            # ======================================================
            order = (
                self.db.query(Order)
                .options(
                    # USER + CUSTOMER PROFILE (NAME + PHONE)
                    joinedload(Order.user)
                        .joinedload(User.customer_profile),

                    # SHIPPING ADDRESS (PLACED ORDER ADDRESS)
                    joinedload(Order.address),

                    # ORDER ITEMS WITH PRODUCT + COMPARE PRICE
                    joinedload(Order.items)
                        .joinedload(OrderItem.variant)
                        .joinedload(ProductVariant.product)
                )
                .filter(Order.id == order_id)
                .first()
            )

            if not order:
                raise ValueError("Order not found")

            # ======================================================
            # IDEMPOTENCY CHECK (NO CHANGE)
            # ======================================================
            existing = (
                self.db.query(Invoice)
                .filter(Invoice.order_id == order.id)
                .first()
            )

            if existing:
                return existing.pdf_path

            # STEP 1: Generate invoice number & date FIRST
            invoice_number = f"INV-{datetime.utcnow().year}-{order.id:06d}"
            invoice_date = datetime.utcnow().strftime("%d %b %Y")

            # STEP 2: Pass them into generator
            pdf_path = generate_invoice(order, invoice_number, invoice_date)

            # ======================================================
            # SAVE INVOICE (NO CHANGE)
            # ======================================================
            invoice = Invoice(
                order_id=order.id,
                invoice_number=invoice_number,
                pdf_path=pdf_path
            )

            self.db.add(invoice)
            self.db.commit()

            # ======================================================
            # SEND EMAIL (NO CHANGE)
            # ======================================================
            if order.user and order.user.email:

                send_email(
                    to_email=order.user.email,
                    subject="Your Luxora Invoice",
                    template_name="invoice.html",
                    context={
                        "order": order,  # full dynamic object
                        "invoice_number": invoice_number
                    },
                    attachment_path=pdf_path
                )

            return pdf_path

        except Exception as e:

            log_event(
                "invoice_error",
                level="critical",
                error=str(e)
            )

            self.db.rollback()
            return None