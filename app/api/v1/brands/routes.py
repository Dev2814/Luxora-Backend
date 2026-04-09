"""
Brand Routes
============

Handles:
• Public brand listing
• Admin brand creation with file upload
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.domains.brands.service import BrandService
from app.api.v1.brands.schemas import BrandResponse

# 🔥 IMPORT STORAGE UTILITY
from app.core.storage import save_file

router = APIRouter(prefix="/brands", tags=["Brands"])


# ======================================================
# LIST BRANDS
# ======================================================

@router.get("/", response_model=List[BrandResponse])
def list_brands(db: Session = Depends(get_db)):

    service = BrandService(db)

    try:
        return service.list_brands()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ======================================================
# CREATE BRAND (ADMIN)
# ======================================================

@router.post("/admin", response_model=BrandResponse)
def create_brand(
    name: str = Form(...),
    meta_title: str = Form(None),
    meta_description: str = Form(None),
    logo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Create brand with:
    • Image upload
    • SEO fields
    """

    service = BrandService(db)

    try:

        # --------------------------------------------------
        # SAVE FILE USING UTILITY
        # --------------------------------------------------
        logo_url = save_file(logo, folder="brands", remove_bg=True)

        return service.create_brand(
            name=name,
            logo_url=logo_url,
            meta_title=meta_title,
            meta_description=meta_description
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))