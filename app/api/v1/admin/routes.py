"""
Admin Routes

Handles admin platform operations.

Architecture:
Route → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.permissions import require_role
from app.domains.admin.service import AdminService

from app.api.v1.admin.schemas import (
    RejectVendorRequest,
    BrandCreate,
    MessageResponse,
    AdminAnalyticsResponse
)

from app.core.logger import log_event


# --------------------------------------------------
# ROUTER
# --------------------------------------------------

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role("admin"))]
)


# --------------------------------------------------
# SERVICE DEPENDENCY
# --------------------------------------------------

def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)


# --------------------------------------------------
# GET PENDING VENDORS
# --------------------------------------------------

@router.get(
    "/vendors/pending",
    summary="List Pending Vendor Approvals"
)
def get_pending_vendors(
    service: AdminService = Depends(get_admin_service)
):

    try:
        return service.get_pending_vendors()

    except ValueError as e:

        log_event(
            "admin_pending_vendors_error",
            level="warning",
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))


# --------------------------------------------------
# APPROVE VENDOR
# --------------------------------------------------

@router.patch(
    "/vendors/{vendor_id}/approve",
    response_model=MessageResponse,
    summary="Approve Vendor Account"
)
def approve_vendor(
    vendor_id: int,
    request: Request,
    service: AdminService = Depends(get_admin_service)
):

    try:

        admin_id = getattr(request.state, "user_id", None)

        return service.approve_vendor(vendor_id, admin_id)

    except ValueError as e:

        log_event(
            "admin_vendor_approve_error",
            level="warning",
            vendor_id=vendor_id,
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))


# --------------------------------------------------
# REJECT VENDOR
# --------------------------------------------------

@router.patch(
    "/vendors/{vendor_id}/reject",
    response_model=MessageResponse,
    summary="Reject Vendor Account"
)
def reject_vendor(
    vendor_id: int,
    payload: RejectVendorRequest,
    request: Request,
    service: AdminService = Depends(get_admin_service)
):

    try:

        admin_id = getattr(request.state, "user_id", None)

        return service.reject_vendor(
            vendor_id,
            payload.reason,
            admin_id
        )

    except ValueError as e:

        log_event(
            "admin_vendor_reject_error",
            level="warning",
            vendor_id=vendor_id,
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))


# --------------------------------------------------
# DEACTIVATE USER
# --------------------------------------------------

@router.patch(
    "/users/{user_id}/deactivate",
    response_model=MessageResponse,
    summary="Deactivate User Account"
)
def deactivate_user(
    user_id: int,
    request: Request,
    service: AdminService = Depends(get_admin_service)
):

    try:

        admin_id = getattr(request.state, "user_id", None)

        return service.deactivate_user(user_id, admin_id)

    except ValueError as e:

        log_event(
            "admin_user_deactivate_error",
            level="warning",
            user_id=user_id,
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))


# --------------------------------------------------
# CREATE BRAND
# --------------------------------------------------

@router.post(
    "/brands",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Brand"
)
def create_brand(
    payload: BrandCreate,
    request: Request,
    service: AdminService = Depends(get_admin_service)
):

    try:

        admin_id = getattr(request.state, "user_id", None)

        return service.create_brand(
            payload.name,
            payload.logo,
            admin_id
        )

    except ValueError as e:

        log_event(
            "admin_brand_create_error",
            level="warning",
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))


# --------------------------------------------------
# LIST BRANDS
# --------------------------------------------------

@router.get(
    "/brands",
    summary="List All Brands"
)
def list_brands(
    service: AdminService = Depends(get_admin_service)
):

    try:
        return service.list_brands()

    except ValueError as e:

        log_event(
            "admin_brand_list_error",
            level="warning",
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))


# --------------------------------------------------
# DELETE BRAND
# --------------------------------------------------

@router.delete(
    "/brands/{brand_id}",
    response_model=MessageResponse,
    summary="Delete Brand"
)
def delete_brand(
    brand_id: int,
    request: Request,
    service: AdminService = Depends(get_admin_service)
):

    try:

        admin_id = getattr(request.state, "user_id", None)

        return service.delete_brand(brand_id, admin_id)

    except ValueError as e:

        log_event(
            "admin_brand_delete_error",
            level="warning",
            brand_id=brand_id,
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))


# --------------------------------------------------
# PLATFORM ANALYTICS
# --------------------------------------------------

@router.get(
    "/analytics",
    response_model=AdminAnalyticsResponse,
    summary="Get Platform Analytics"
)
def get_platform_stats(
    service: AdminService = Depends(get_admin_service)
):

    try:
        return service.get_platform_stats()

    except ValueError as e:

        log_event(
            "admin_platform_stats_error",
            level="warning",
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))