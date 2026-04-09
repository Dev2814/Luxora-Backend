"""
Invoice Service
===============

Responsible for handling invoice lifecycle operations.

Responsibilities
----------------
• Generate invoice PDF for completed orders
• Store invoice record in database
• Send invoice to customer via email
• Ensure invoice delivery does not break payment workflow
• Provide clean abstraction between payment and invoice systems
"""

from datetime import datetime

from app.infrastructure.invoice.generator import generate_invoice
from app.infrastructure.email.service import send_email
from app.core.logger import log_event
from app.models.invoice import Invoice


class InvoiceService:
    """
    Service responsible for generating and delivering invoices.
    """

    def __init__(self, db):
        """
        Initialize invoice service with database session.
        """
        self.db = db

    def create_invoice(self, order):
        """
        Generate invoice PDF, store metadata in database,
        and send invoice email to customer.
        """

        try:

            # --------------------------------------------------
            # STEP 1 — GENERATE INVOICE NUMBER
            # --------------------------------------------------

            year = datetime.utcnow().year
            invoice_number = f"INV-{year}-{order.id:06d}"

            # --------------------------------------------------
            # STEP 2 — GENERATE PDF
            # --------------------------------------------------

            pdf_path = generate_invoice(order)

            # --------------------------------------------------
            # STEP 3 — STORE INVOICE IN DATABASE
            # --------------------------------------------------

            invoice = Invoice(
                order_id=order.id,
                invoice_number=invoice_number,
                pdf_path=pdf_path
            )

            self.db.add(invoice)
            self.db.commit()

            log_event(
                "invoice_generated",
                order_id=order.id,
                invoice_number=invoice_number,
                pdf_path=pdf_path
            )

            # --------------------------------------------------
            # STEP 4 — DETERMINE CUSTOMER NAME
            # --------------------------------------------------

            customer_name = "Customer"

            if order.user and order.user.customer_profile:
                customer_name = order.user.customer_profile.full_name

            # --------------------------------------------------
            # STEP 5 — SEND EMAIL
            # --------------------------------------------------

            to_email = order.user.email if order.user else None

            email_sent = False

            if to_email:

                email_sent = send_email(
                    to_email=to_email,
                    subject="Your Luxora Invoice",
                    template_name="invoice.html",
                    context={
                        "title": "Luxora Invoice",
                        "order": order,
                        "customer_name": customer_name,
                        "invoice_number": invoice_number
                    },
                    attachment_path=pdf_path
                )

            # --------------------------------------------------
            # STEP 6 — LOG EMAIL RESULT
            # --------------------------------------------------

            if email_sent:

                log_event(
                    "invoice_email_sent",
                    order_id=order.id,
                    email=to_email
                )

            else:

                log_event(
                    "invoice_email_failed",
                    level="warning",
                    order_id=order.id,
                    email=to_email
                )

            return pdf_path

        except Exception as e:

            # --------------------------------------------------
            # FAIL SAFE
            # --------------------------------------------------
            # Invoice failure must NOT break payment workflow
            # --------------------------------------------------

            log_event(
                "invoice_generation_failed",
                level="error",
                order_id=order.id,
                error=str(e)
            )

            return None