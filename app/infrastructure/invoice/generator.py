"""
Enterprise Invoice Generator
============================

Generates professional PDF invoices for Luxora orders.

Features
--------
• Professional invoice layout
• Luxora branding
• Product table
• Indian Rupee currency formatting
• Invoice numbering
• QR code verification
• Automatic page handling
• Production‑grade formatting
"""

import os
from datetime import datetime

import qrcode

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


RUPEE = "₹"


def format_inr(amount):
    return f"{RUPEE}{float(amount):,.2f}"


def generate_invoice(order):
    """
    Generate professional invoice PDF for an order.
    """

    # --------------------------------------------------
    # Invoice Directory
    # --------------------------------------------------

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INVOICE_DIR = os.path.join(BASE_DIR, "../../../invoices")

    os.makedirs(INVOICE_DIR, exist_ok=True)

    year = datetime.utcnow().year
    invoice_number = f"INV-{year}-{order.id:06d}"

    file_path = os.path.join(INVOICE_DIR, f"{invoice_number}.pdf")

    # --------------------------------------------------
    # QR CODE (order verification)
    # --------------------------------------------------

    qr_data = f"Luxora Order Verification\nOrder ID: {order.id}\nInvoice: {invoice_number}"

    qr = qrcode.make(qr_data)

    qr_path = os.path.join(INVOICE_DIR, f"{invoice_number}_qr.png")
    qr.save(qr_path)

    # --------------------------------------------------
    # PDF Document
    # --------------------------------------------------

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    elements = []

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    title = Paragraph(
        "<b>Luxora</b>",
        styles["Title"]
    )

    elements.append(title)
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            f"<b>Invoice Number:</b> {invoice_number}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Invoice Date:</b> {datetime.utcnow().strftime('%d %b %Y')}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 20))

    # --------------------------------------------------
    # CUSTOMER INFORMATION
    # --------------------------------------------------

    customer_name = "Customer"

    if order.user and order.user.customer_profile:
        customer_name = order.user.customer_profile.full_name

    customer_info = [
        ["Bill To:", ""],
        ["Name", customer_name],
        ["Email", order.user.email if order.user else "-"],
    ]

    table = Table(customer_info, colWidths=[100, 350])

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey)
    ]))

    elements.append(table)

    elements.append(Spacer(1, 20))

    # --------------------------------------------------
    # PRODUCT TABLE
    # --------------------------------------------------

    data = [
        ["#", "Product", "Quantity", "Price", "Subtotal"]
    ]

    index = 1
    total = 0

    for item in order.items:

        product_name = getattr(item.variant.product, "name", "Product")

        subtotal = float(item.price_snapshot) * item.quantity

        total += subtotal

        data.append([
            index,
            product_name,
            item.quantity,
            format_inr(item.price_snapshot),
            format_inr(subtotal)
        ])

        index += 1

    product_table = Table(data, colWidths=[40, 200, 80, 100, 100])

    product_table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.black),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

        ("ALIGN", (2,1), (-1,-1), "CENTER"),

    ]))

    elements.append(product_table)

    elements.append(Spacer(1, 20))

    # --------------------------------------------------
    # TOTAL SECTION
    # --------------------------------------------------

    tax = total * 0.18
    grand_total = total + tax

    totals = [
        ["Subtotal", format_inr(total)],
        ["GST (18%)", format_inr(tax)],
        ["Grand Total", format_inr(grand_total)]
    ]

    totals_table = Table(totals, colWidths=[300, 150])

    totals_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,2), (-1,2), colors.lightgrey)
    ]))

    elements.append(totals_table)

    elements.append(Spacer(1, 30))

    # --------------------------------------------------
    # QR CODE
    # --------------------------------------------------

    elements.append(
        Paragraph("<b>Order Verification QR</b>", styles["Normal"])
    )

    elements.append(Image(qr_path, width=80, height=80))

    elements.append(Spacer(1, 20))

    # --------------------------------------------------
    # FOOTER
    # --------------------------------------------------

    elements.append(
        Paragraph(
            "Thank you for shopping with Luxora.",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            "This is a computer generated invoice.",
            styles["Italic"]
        )
    )

    # --------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------

    doc.build(elements)

    return file_path