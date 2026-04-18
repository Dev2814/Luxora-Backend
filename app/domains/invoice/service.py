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
from app.models import order
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.user import User
from app.models.customer_profile import CustomerProfile
from app.core.logger import log_event
from app.domains.invoice.repository import InvoiceRepository
import uuid


class InvoiceService:

    def __init__(self, db):
        self.db = db
        self.repo = InvoiceRepository(db)

    def generate_invoice_number(self) -> str:
        """
        Generate unique invoice number.

        Format: INV-2026-XXXXXX
        """
        return f"INV-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}"


    def create_invoice(self, order_id: int):

        try:
            # ============================================
            # LOAD ORDER WITH RELATIONS (OPTIMIZED)
            # ============================================
            order = (
                self.db.query(Order)
                .options(
                    joinedload(Order.items)
                    .joinedload(OrderItem.variant)
                    .joinedload(ProductVariant.product),
                    joinedload(Order.user)
                )
                .filter(Order.id == order_id)
                .first()
            )

            # ============================================
            # 🚨 VALIDATIONS
            # ============================================
            if not order:
                raise ValueError("Order not found")

            if order.payment_status != "paid":
                raise ValueError("Invoice cannot be created before payment")

            if order.total_amount <= 0:
                raise ValueError("Invalid order total amount")

            # Prevent duplicate
            existing = self.repo.get_by_order(order_id)
            if existing:
                return existing

            # ============================================
            # GENERATE INVOICE NUMBER FIRST
            # ============================================
            invoice_number = self.generate_invoice_number()
            invoice_date = datetime.utcnow()

            # ============================================
            # GENERATE PDF FIRST (CRITICAL FIX)
            # ============================================
            pdf_path = generate_invoice(
                order,
                invoice_number,
                invoice_date
            )

            # ============================================
            # NOW CREATE INVOICE (SAFE)
            # ============================================
            invoice = Invoice(
                order_id=order.id,
                invoice_number=invoice_number,
                total_amount=order.total_amount,
                pdf_path=pdf_path  
            )

            self.db.add(invoice)
            self.db.commit()
            self.db.refresh(invoice)

            # ============================================
            # SEND EMAIL (NON-BLOCKING FAILURE)
            # ============================================
            try:
                if order.user and order.user.email:

                    send_email(
                        to_email=order.user.email,
                        subject=f"Your Invoice {invoice.invoice_number}",
                        template_name="invoice_email.html",
                        context={
                            "title": f"Invoice {invoice_number}",
                            "customer_name": order.user.customer_profile.full_name if order.user.customer_profile else "Valued Customer",
                            "order": order,
                            "download_link": f"http://localhost:2814/api/v1/invoices/{order.order_number}/download",
                            "year": datetime.utcnow().year
                        },
                        attachment_path=pdf_path
                    )

                else:
                    log_event(
                        "invoice_email_skipped",
                        order_id=order.id
                    )

            except Exception as email_error:
                log_event(
                    "invoice_email_failed",
                    level="error",
                    order_id=order.id,
                    error=str(email_error)
                )

            # ============================================
            # SUCCESS LOG
            # ============================================
            log_event(
                "invoice_created",
                order_id=order.id,
                invoice_number=invoice.invoice_number,
                total_amount=str(order.total_amount)
            )

            return invoice

        except Exception as e:

            self.db.rollback()

            log_event(
                "invoice_creation_failed",
                level="critical",
                order_id=order_id,
                error=str(e)
            )

            raise
        
    # =========================================================
    # GET INVOICE
    # =========================================================

    def get_invoice(self, order_id: int, user_id: int):
        invoice = self.repo.get_by_order(order_id)

        if not invoice:
            raise ValueError("Invoice not found")

        if invoice.order.user_id != user_id:
            raise ValueError("Unauthorized")

        return {
            "invoice_number": invoice.invoice_number,
            "order_id": invoice.order_id,
            "total_amount": float(invoice.total_amount),
            "pdf_path": invoice.pdf_path,
            "created_at": str(invoice.created_at)
        }


    def list_user_invoices(self, user_id: int):
        invoices = self.repo.get_by_user(user_id)

        return [
            {
                "invoice_number": inv.invoice_number,
                "order_id": inv.order_id,
                "total_amount": float(inv.total_amount),
                "created_at": str(inv.created_at)
            }
            for inv in invoices
        ]