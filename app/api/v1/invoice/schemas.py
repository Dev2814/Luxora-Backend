"""
Invoice Schemas
===============

Handles request/response validation for invoice APIs.

Design:
-------
• Strict response contracts
• API consistency
• Future extensibility
"""

from pydantic import BaseModel
from typing import List


# =========================================================
# SINGLE INVOICE RESPONSE
# =========================================================

class InvoiceResponse(BaseModel):
    invoice_number: str
    order_id: int
    total_amount: float
    pdf_path: str
    created_at: str


# =========================================================
# INVOICE LIST ITEM
# =========================================================

class InvoiceListItem(BaseModel):
    invoice_number: str
    order_id: int
    total_amount: float
    created_at: str


# =========================================================
# INVOICE LIST RESPONSE
# =========================================================

class InvoiceListResponse(BaseModel):
    items: List[InvoiceListItem]