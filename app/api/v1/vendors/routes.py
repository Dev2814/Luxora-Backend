"""
Vendor Routes

Handles vendor-related API endpoints.

Responsibilities:
- Vendor application
- Vendor profile management
- Vendor product management

Architecture:

Client
   ↓
Routes
   ↓
VendorService
   ↓
VendorRepository
   ↓
Database
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.permissions import require_role
from app.api.deps_auth import get_current_user

from app.domains.vendors.service import VendorService

from app.api.v1.vendors.schemas import (
    VendorApply,
    VendorUpdate,
    VendorProfileResponse,
    VendorProductListResponse,
    UpdateProductSchema
)

router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"]
)

# ======================================================
# VENDOR APPLY
# ======================================================

@router.post(
    "/apply",
    summary="Apply to become a vendor"
)
def apply_vendor(
    payload: VendorApply,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows a registered user to apply as a vendor.
    """

    service = VendorService(db)

    try:
        return service.apply_vendor(
            user["user_id"],
            payload
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ======================================================
# GET VENDOR PROFILE
# ======================================================

@router.get(
    "/me",
    response_model=VendorProfileResponse,
    dependencies=[Depends(require_role("vendor"))],
    summary="Get Vendor Profile"
)
def get_vendor_profile(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the authenticated vendor profile.
    """

    service = VendorService(db)

    try:
        return service.get_vendor_profile(user["user_id"])

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ======================================================
# UPDATE VENDOR PROFILE
# ======================================================

@router.put(
    "/me",
    response_model=VendorProfileResponse,
    dependencies=[Depends(require_role("vendor"))],
    summary="Update Vendor Profile"
)
def update_vendor_profile(
    payload: VendorUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update vendor store information.
    """

    service = VendorService(db)

    try:
        return service.update_vendor_profile(
            user["user_id"],
            payload
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ======================================================
# LIST VENDOR PRODUCTS
# ======================================================

@router.get(
    "/products",
    response_model=VendorProductListResponse,
    dependencies=[Depends(require_role("vendor"))],
    summary="List Vendor Products"
)
def get_vendor_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve products owned by the authenticated vendor.
    """

    service = VendorService(db)

    try:
        return service.get_vendor_products(
            user["user_id"],
            page,
            limit
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ======================================================
# GET SINGLE VENDOR PRODUCT
# ======================================================

@router.get(
    "/products/{product_id}",
    dependencies=[Depends(require_role("vendor"))],
    summary="Get Vendor Product"
)
def get_vendor_product(
    product_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific product belonging to the vendor.
    """

    service = VendorService(db)

    try:
        return service.get_vendor_product(
            user["user_id"],
            product_id
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ======================================================
# UPDATE VENDOR PRODUCT
# ======================================================

@router.put(
    "/products/{product_id}",
    dependencies=[Depends(require_role("vendor"))],
    summary="Update Vendor Product"
)
def update_vendor_product(
    product_id: int,
    payload: UpdateProductSchema,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update product owned by the vendor.
    """

    service = VendorService(db)

    try:
        return service.update_vendor_product(
            user["user_id"],
            product_id,
            payload
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/products/{product_id}",
    dependencies=[Depends(require_role("vendor"))],
    summary="Delete Vendor Product",
    response_model=dict   # ✅ ADD THIS
)
def delete_vendor_product(
    product_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a product owned by the vendor.

    - Validates vendor ownership
    - Performs soft delete
    - Returns confirmation message
    """

    service = VendorService(db)

    try:
        return service.delete_vendor_product(
            user["user_id"],
            product_id
        )

    except ValueError as e:
        # ✅ Correct semantic error
        raise HTTPException(status_code=404, detail=str(e))

    except Exception:
        # ✅ Fallback (enterprise safety)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )