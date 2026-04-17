"""
Enterprise Invoice Generator — Luxora
======================================

Production-grade PDF invoice.

Features
--------
• Custom canvas header / footer on every page   (navy #0D1B2A + gold #C9A84C)
• Two-column Bill-To ↔ Invoice-Details card
• Alternating-row product table (SKU + variant sub-line)
• CGST / SGST split, Grand Total highlighted in navy-gold
• In-memory QR code — no temp files written to disk
• "Page X of Y" resolved via two-pass canvas
• invoice_number + invoice_date injected by InvoiceService
  (single source of truth — generator never recomputes them)

Public API
----------
    pdf_path = generate_invoice(order, invoice_number, invoice_date)
"""

import io
import os
from datetime import datetime

import qrcode
from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ── Try to read INVOICE_DIR from environment; fall back to sibling "invoices/" ──
_HERE = os.path.dirname(os.path.abspath(__file__))
INVOICE_DIR: str = os.environ.get(
    "LUXORA_INVOICE_DIR",
    os.path.normpath(os.path.join(_HERE, "../../../invoices")),
)

# ─────────────────────────────────────────────
#  BRAND PALETTE
# ─────────────────────────────────────────────

NAVY       = colors.HexColor("#0D1B2A")
GOLD       = colors.HexColor("#C9A84C")
GOLD_LIGHT = colors.HexColor("#F5E6C8")
OFFWHITE   = colors.HexColor("#FAFAFA")
LIGHT_GREY = colors.HexColor("#F2F2F2")
MID_GREY   = colors.HexColor("#CCCCCC")
DARK_GREY  = colors.HexColor("#444444")
WHITE      = colors.white
BLACK      = colors.black

RUPEE = "\u20B9"  # ₹

PAGE_W, PAGE_H = A4
MARGIN         = 18 * mm
HEADER_H       = 38 * mm
FOOTER_H       = 20 * mm


# ─────────────────────────────────────────────
#  CURRENCY HELPER
# ─────────────────────────────────────────────

def _fmt_inr(amount: float) -> str:
    """Format a number using Indian comma grouping  e.g. ₹1,23,456.00"""
    integer_str, decimal_str = f"{abs(float(amount)):.2f}".split(".")
    if len(integer_str) > 3:
        last3 = integer_str[-3:]
        rest  = integer_str[:-3]
        groups: list[str] = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        integer_str = ",".join(groups) + "," + last3
    return f"{RUPEE}{integer_str}.{decimal_str}"


# ─────────────────────────────────────────────
#  QR CODE — in-memory, no temp file
# ─────────────────────────────────────────────

def _make_qr_buf(data: str, size_px: int = 280) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img: PILImage.Image = (
        qr.make_image(fill_color="#0D1B2A", back_color="white")
        .convert("RGB")
    )
    img = img.resize((size_px, size_px), PILImage.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────
#  PARAGRAPH STYLES
# ─────────────────────────────────────────────

def _build_styles() -> dict:
    BF = "Helvetica-Bold"
    RF = "Helvetica"
    RI = "Helvetica-Oblique"

    return {
        "section_heading": ParagraphStyle("section_heading", fontName=BF, fontSize=7.5,
                                          textColor=GOLD, leading=10, spaceAfter=4,
                                          alignment=TA_LEFT),
        "info_key":        ParagraphStyle("info_key",        fontName=BF, fontSize=8,
                                          textColor=DARK_GREY, leading=13),
        "info_val":        ParagraphStyle("info_val",        fontName=RF, fontSize=8.5,
                                          textColor=BLACK, leading=13),
        "th":              ParagraphStyle("th",              fontName=BF, fontSize=8,
                                          textColor=WHITE, alignment=TA_CENTER),
        "td":              ParagraphStyle("td",              fontName=RF, fontSize=8.5,
                                          textColor=DARK_GREY, leading=12),
        "td_c":            ParagraphStyle("td_c",            fontName=RF, fontSize=8.5,
                                          textColor=DARK_GREY, leading=12, alignment=TA_CENTER),
        "td_r":            ParagraphStyle("td_r",            fontName=RF, fontSize=8.5,
                                          textColor=DARK_GREY, leading=12, alignment=TA_RIGHT),
        "total_k":         ParagraphStyle("total_k",         fontName=RF, fontSize=9,
                                          textColor=DARK_GREY, leading=14, alignment=TA_RIGHT),
        "total_v":         ParagraphStyle("total_v",         fontName=RF, fontSize=9,
                                          textColor=DARK_GREY, leading=14, alignment=TA_RIGHT),
        "grand_k":         ParagraphStyle("grand_k",         fontName=BF, fontSize=11,
                                          textColor=WHITE, leading=16, alignment=TA_RIGHT),
        "grand_v":         ParagraphStyle("grand_v",         fontName=BF, fontSize=11,
                                          textColor=GOLD, leading=16, alignment=TA_RIGHT),
        "qr_label":        ParagraphStyle("qr_label",        fontName=BF, fontSize=7.5,
                                          textColor=DARK_GREY, alignment=TA_CENTER, leading=11),
        "terms":           ParagraphStyle("terms",           fontName=RF, fontSize=7.5,
                                          textColor=DARK_GREY, leading=11),
    }


# ─────────────────────────────────────────────
#  CANVAS — two-pass for correct "Page X of Y"
# ─────────────────────────────────────────────

class _LuxoraCanvas(rl_canvas.Canvas):
    """
    Defers showPage so total page count is known before anything is drawn.
    Header and footer are painted in the final save() pass.
    """

    def __init__(self, *args, invoice_number: str = "", invoice_date: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._invoice_number = invoice_number
        self._invoice_date   = invoice_date
        self._saved_states: list[dict] = []

    # Intercept each page — buffer its state instead of flushing
    def showPage(self):
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self._draw_header()
            self._draw_footer(self._pageNumber, total_pages)
            super().showPage()
        super().save()

    # ── Header ──────────────────────────────────────────────────────────────
    def _draw_header(self) -> None:
        # Navy band
        self.setFillColor(NAVY)
        self.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)

        # Gold rule below the band
        self.setFillColor(GOLD)
        self.rect(0, PAGE_H - HEADER_H - 1.5 * mm, PAGE_W, 1.5 * mm, fill=1, stroke=0)

        # Brand name
        self.setFillColor(WHITE)
        self.setFont("Helvetica-Bold", 26)
        self.drawString(MARGIN, PAGE_H - 18 * mm, "LUXORA")

        # Tagline
        self.setFillColor(GOLD)
        self.setFont("Helvetica", 8)
        self.drawString(MARGIN, PAGE_H - 24 * mm, "PREMIUM FASHION  ·  EST. 2024")

        # "INVOICE" label (right)
        self.setFillColor(WHITE)
        self.setFont("Helvetica-Bold", 20)
        self.drawRightString(PAGE_W - MARGIN, PAGE_H - 16 * mm, "INVOICE")

        # Invoice number
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(GOLD)
        self.drawRightString(PAGE_W - MARGIN, PAGE_H - 23 * mm, self._invoice_number)

        # Invoice date
        self.setFont("Helvetica", 8)
        self.setFillColor(MID_GREY)
        self.drawRightString(PAGE_W - MARGIN, PAGE_H - 29 * mm, self._invoice_date)

    # ── Footer ──────────────────────────────────────────────────────────────
    def _draw_footer(self, page_num: int, total_pages: int) -> None:
        y_rule = FOOTER_H - 6 * mm + 8 * mm

        # Rule
        self.setStrokeColor(MID_GREY)
        self.setLineWidth(0.5)
        self.line(MARGIN, y_rule, PAGE_W - MARGIN, y_rule)

        # Thank-you
        self.setFont("Helvetica", 8)
        self.setFillColor(DARK_GREY)
        self.drawCentredString(
            PAGE_W / 2, y_rule - 4 * mm,
            "Thank you for shopping with Luxora — your style, our passion.",
        )

        # Legal note
        self.setFont("Helvetica-Oblique", 7)
        self.setFillColor(MID_GREY)
        self.drawCentredString(
            PAGE_W / 2, y_rule - 8 * mm,
            "This is a computer-generated invoice and requires no signature.",
        )

        # Page number
        self.setFont("Helvetica", 7.5)
        self.drawRightString(PAGE_W - MARGIN, y_rule - 8 * mm, f"Page {page_num} of {total_pages}")


# ─────────────────────────────────────────────
#  MAIN PUBLIC FUNCTION
# ─────────────────────────────────────────────

def generate_invoice(order, invoice_number: str, invoice_date: str) -> str:
    """
    Generate a production-grade Luxora invoice PDF.

    Parameters
    ----------
    order          : ORM Order object.
                     Expects: .id, .user (.email, .customer_profile),
                              .items (.variant.product.name, .variant.sku,
                                      .variant.name, .price_snapshot, .quantity),
                              .status
    invoice_number : Pre-computed invoice number from InvoiceService.
    invoice_date   : Formatted date string from InvoiceService  (e.g. "17 Apr 2026").

    Returns
    -------
    str : Absolute path to the generated PDF file.

    Raises
    ------
    Any exception from reportlab / IO is allowed to propagate so that
    InvoiceService can catch it and log it correctly.
    """

    os.makedirs(INVOICE_DIR, exist_ok=True)

    file_path = os.path.join(INVOICE_DIR, f"{invoice_number}.pdf")

    S = _build_styles()

    # QR code (in-memory)
    qr_data = (
        f"Luxora Order Verification\n"
        f"Order ID  : #LUX-ORD-{order.id}\n"
        f"Invoice   : #LUX-INV-{invoice_number}\n"
        f"Date      : {invoice_date}"
    )
    qr_buf = _make_qr_buf(qr_data)

    # ── Document layout ────────────────────────────────────────────────────
    content_frame = Frame(
        MARGIN,
        FOOTER_H + 2 * mm,
        PAGE_W - 2 * MARGIN,
        PAGE_H - HEADER_H - 2 * mm - FOOTER_H - 4 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=4 * mm,
        bottomPadding=0,
    )

    def _canvas_factory(*args, **kwargs):
        return _LuxoraCanvas(
            *args,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            **kwargs,
        )

    doc = BaseDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=HEADER_H + 4 * mm,
        bottomMargin=FOOTER_H + 4 * mm,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[content_frame])])

    el = []   # flowable elements

    # ── Bill-To + Invoice Details card ────────────────────────────────────

    # Safely extract customer fields
    customer_name    = "Customer"
    customer_email   = order.user.email if order.user else "-"
    customer_phone   = order.user.phone if order.user else "-"
    shipping_address = "-"

    if order.user and order.user.customer_profile:
        cp = order.user.customer_profile
        customer_name    = getattr(cp, "full_name", "Customer") or "Customer"
        # Phone should always come from User model
        # customer_phone = order.user.phone if order.user else "-"
        # shipping_address = getattr(cp, "address",   "-")        or "-"

        if hasattr(order, "address") and order.address:
            shipping_address = f"{order.address.address_line1}, {order.address.city}, {order.address.state}"

    def _kv_row(key: str, val: str) -> Table:
        t = Table(
            [[Paragraph(key, S["info_key"]), Paragraph(val, S["info_val"])]],
            colWidths=[22 * mm, 55 * mm],
        )
        t.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        return t

    bill_panel = [
        Paragraph("BILL TO", S["section_heading"]),
        _kv_row("Name",    customer_name),
        _kv_row("Email",   customer_email),
        _kv_row("Phone",   customer_phone),
        _kv_row("Address", shipping_address),
    ]

    order_status = getattr(order, "status", "confirmed")
    status_label = str(order_status).replace("_", " ").title() if order_status else "Confirmed"

    detail_rows = [
        [Paragraph("Order ID",   S["info_key"]), Paragraph(f"#{order.id}",   S["info_val"])],
        [Paragraph("Invoice No", S["info_key"]), Paragraph(invoice_number,   S["info_val"])],
        [Paragraph("Date",       S["info_key"]), Paragraph(invoice_date,     S["info_val"])],
        [Paragraph("Status",     S["info_key"]), Paragraph(status_label,     S["info_val"])],
        [Paragraph("Currency",   S["info_key"]), Paragraph(f"INR ({RUPEE})", S["info_val"])],
        [Paragraph("Payment", S["info_key"]), Paragraph(getattr(order, "payment_method", "Online"), S["info_val"])],
    ]
    detail_table = Table(detail_rows, colWidths=[24 * mm, 52 * mm])
    detail_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    right_panel = [Paragraph("INVOICE DETAILS", S["section_heading"]), detail_table]

    CW       = PAGE_W - 2 * MARGIN
    half_col = CW / 2 - 4 * mm

    info_outer = Table(
        [[bill_panel, right_panel]],
        colWidths=[half_col + 8 * mm, half_col],
    )
    info_outer.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    info_card = Table([[info_outer]], colWidths=[CW])
    info_card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_GREY),
        ("ROUNDEDCORNERS",(0, 0), (-1, -1), [4, 4, 4, 4]),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8 * mm),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8 * mm),
        ("TOPPADDING",    (0, 0), (-1, -1), 5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
    ]))

    el.append(info_card)
    el.append(Spacer(1, 6 * mm))
    el.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY, spaceAfter=4 * mm))

    # ── Order Items table ──────────────────────────────────────────────────

    el.append(Paragraph("ORDER ITEMS", S["section_heading"]))
    el.append(Spacer(1, 2 * mm))

    # col_widths = [8 * mm, CW * 0.40, 18 * mm, CW * 0.18, CW * 0.20]
    col_widths = [
        8 * mm,        # #
        CW * 0.28,     # PRODUCT
        18 * mm,       # QTY
        CW * 0.14,     # MRP
        CW * 0.14,     # PRICE
        CW * 0.13,     # DISCOUNT
        CW * 0.13      # SUBTOTAL
    ]

    header_row = [
        Paragraph("#",          S["th"]),
        Paragraph("PRODUCT",    S["th"]),
        Paragraph("QTY",        S["th"]),
        Paragraph("MRP",        S["th"]),          # compare_price
        Paragraph("PRICE",      S["th"]),          # selling price
        Paragraph("DISCOUNT",   S["th"]),          # new
        Paragraph("SUBTOTAL",   S["th"]),
    ]
    rows  = [header_row]
    total = 0.0
    total_discount = 0.0

    for idx, item in enumerate(order.items, start=1):
        product_name = getattr(item.variant.product, "name", "Product")
        sku          = getattr(item.variant, "sku",  None)
        variant_name = getattr(item.variant, "name", None)

        name_para = Paragraph(f"<b>{product_name}</b>", S["td"])
        sub_parts = []
        if variant_name:
            sub_parts.append(variant_name)
        if sku:
            sub_parts.append(f"SKU: {sku}")

        if sub_parts:
            sub_para  = Paragraph(
                f'<font size="7" color="#888888">{" · ".join(sub_parts)}</font>',
                S["td"],
            )
            prod_cell = [name_para, sub_para]
        else:
            prod_cell = name_para

        unit_price = float(item.price_snapshot)
        compare_price = float(getattr(item.variant.product, "compare_price", 0) or 0)
        quantity = item.quantity
        discount_per_unit = compare_price - unit_price if compare_price > unit_price else 0
        discount = discount_per_unit * quantity
        
        subtotal = unit_price * quantity
        total += subtotal
        total_discount += discount 

        rows.append([        
            Paragraph(str(idx),             S["td_c"]),
            prod_cell,
            Paragraph(str(quantity),        S["td_c"]),
            Paragraph(_fmt_inr(compare_price), S["td_r"]),
            Paragraph(_fmt_inr(unit_price), S["td_r"]),
             Paragraph(_fmt_inr(discount), S["td_r"]),
            Paragraph(_fmt_inr(subtotal),   S["td_r"]),
        ])

    product_table = Table(rows, colWidths=col_widths, repeatRows=1)

    ts = [
        ("BACKGROUND",    (0,  0), (-1,  0), NAVY),
        ("TEXTCOLOR",     (0,  0), (-1,  0), WHITE),
        ("TOPPADDING",    (0,  0), (-1,  0), 4 * mm),
        ("BOTTOMPADDING", (0,  0), (-1,  0), 4 * mm),
        ("LEFTPADDING",   (0,  0), (-1, -1), 3 * mm),
        ("RIGHTPADDING",  (0,  0), (-1, -1), 3 * mm),
        ("TOPPADDING",    (0,  1), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0,  1), (-1, -1), 3 * mm),
        ("VALIGN",        (0,  0), (-1, -1), "MIDDLE"),
        ("LINEBELOW",     (0,  0), (-1, -2), 0.3, MID_GREY),
        ("LINEBELOW",     (0, -1), (-1, -1), 1,   NAVY),
    ]
    for i in range(1, len(rows)):
        ts.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY if i % 2 == 0 else WHITE))
    product_table.setStyle(TableStyle(ts))

    el.append(product_table)
    el.append(Spacer(1, 6 * mm))

    # ── Totals + QR side-by-side ───────────────────────────────────────────

    grand_total = total

    totals_data = [
        [Paragraph("Subtotal",                S["total_k"]), Paragraph(_fmt_inr(total),       S["total_v"])],
        [Paragraph("Total Discount", S["total_k"]), Paragraph(_fmt_inr(total_discount), S["total_v"])],
        # [Paragraph("CGST (9%)",               S["total_k"]), Paragraph(_fmt_inr(tax / 2),     S["total_v"])],
        # [Paragraph("SGST (9%)",               S["total_k"]), Paragraph(_fmt_inr(tax / 2),     S["total_v"])],
        [Paragraph("Grand Total ", S["grand_k"]), Paragraph(_fmt_inr(grand_total), S["grand_v"])],
    ]
    totals_table = Table(totals_data, colWidths=[60 * mm, 38 * mm])
    totals_table.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING",    (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),

        # 🔥 Always target LAST ROW dynamically
        ("BACKGROUND",    (0, -1), (-1, -1), NAVY),
        ("TOPPADDING",    (0, -1), (-1, -1), 4 * mm),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 4 * mm),
        ("ROUNDEDCORNERS",(0, -1), (-1, -1), [4, 4, 4, 4]),
    ]))

    qr_img   = Image(qr_buf, width=24 * mm, height=24 * mm)
    qr_panel = Table([[qr_img], [Paragraph("Scan to verify", S["qr_label"])]], colWidths=[30 * mm])
    qr_panel.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    spacer_w = CW - 98 * mm - 6 * mm - 32 * mm
    bottom   = Table(
        [[Spacer(1, 1), totals_table, Spacer(6 * mm, 1), qr_panel]],
        colWidths=[spacer_w, 98 * mm, 6 * mm, 32 * mm],
    )
    bottom.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    el.append(bottom)
    el.append(Spacer(1, 6 * mm))

    # ── Terms strip ───────────────────────────────────────────────────────

    terms = Table(
        [[Paragraph(
            "<b>Terms &amp; Conditions</b><br/>"
            "<font size='7'>All prices are inclusive of applicable taxes. "
            "Returns accepted within 15 days of delivery. "
            "For support: support@luxora.in  |  1800-XXX-XXXX</font>",
            S["terms"],
        )]],
        colWidths=[CW],
    )
    terms.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GOLD_LIGHT),
        ("ROUNDEDCORNERS",(0, 0), (-1, -1), [4, 4, 4, 4]),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6 * mm),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6 * mm),
        ("TOPPADDING",    (0, 0), (-1, -1), 4 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
    ]))

    el.append(KeepTogether(terms))

    # ── Build PDF ─────────────────────────────────────────────────────────

    doc.build(el, canvasmaker=_canvas_factory)

    return file_path