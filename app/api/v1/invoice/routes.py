"""
Invoice Routes
==============

Handles invoice retrieval and download.

Features:
---------
• Get invoice details
• Download invoice PDF
• List user invoices
"""

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.api.v1.invoice.schemas import (
    InvoiceResponse,
    InvoiceListResponse
)

from app.domains.invoice.service import InvoiceService
from app.core.logger import log_event

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)


# =========================================================
# SERVICE DEPENDENCY
# =========================================================

def get_invoice_service(db: Session = Depends(get_db)):
    return InvoiceService(db)


# =========================================================
# GET INVOICE DETAILS
# =========================================================

@router.get("/{order_id}")
def get_invoice(
    order_id: int,
    service: InvoiceService = Depends(get_invoice_service),
    current_user=Depends(get_current_user)
):
    try:
        invoice = service.get_invoice(order_id, current_user["user_id"])

        return InvoiceResponse(**invoice)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================
# DOWNLOAD INVOICE
# =========================================================

@router.get("/{order_id}/download")
def download_invoice(
    order_id: int,
    service: InvoiceService = Depends(get_invoice_service),
    current_user=Depends(get_current_user)
):
    try:
        invoice = service.get_invoice(order_id, current_user["user_id"])

        # if not invoice.get("pdf_path"):
        #     raise HTTPException(status_code=404, detail="Invoice file not found")
        pdf_path = invoice.get("pdf_path")

        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="Invoice file not found")
        
        file_name = os.path.basename(invoice["pdf_path"])

        return FileResponse(
            path=invoice["pdf_path"],
            media_type="application/pdf",
            filename=file_name,
            headers={
                "Content-Disposition": f"attachment; filename={file_name}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================
# LIST USER INVOICES
# =========================================================

@router.get("/")
def list_invoices(
    service: InvoiceService = Depends(get_invoice_service),
    current_user=Depends(get_current_user)
):
    invoices = service.list_user_invoices(current_user["user_id"])
    
    return InvoiceListResponse(items=invoices)