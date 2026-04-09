"""
Coupon Routes
=============

API endpoints for coupon system.

Features
--------
• Apply coupon before checkout
• Validate coupon
• Clean response structure
• Production-grade error handling

Architecture
------------
Client → Routes → Service → Repository → DB
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user

from app.domains.coupons.service import CouponService
from app.api.v1.coupons.schemas import (
    ApplyCouponRequest,
    ApplyCouponResponse,
    ValidateCouponResponse,
    MessageResponse,
    CouponCreateRequest
)

from app.core.logger import log_event


router = APIRouter(
    prefix="/coupons",
    tags=["Coupons"]
)

# ======================================================
# DEPENDENCY
# ======================================================

def get_service(db: Session = Depends(get_db)) -> CouponService:
    return CouponService(db)

# ======================================================
# CREATE COUPON (ADMIN)
# ======================================================

@router.post(
    "/admin",
    response_model=MessageResponse,
    summary="Create coupon (Admin only)"
)
def create_coupon(
    payload: CouponCreateRequest,
    service: CouponService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Create a new coupon.

    ⚠️ Admin only
    """

    # --------------------------------------------------
    # ROLE CHECK (CRITICAL)
    # --------------------------------------------------

    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create coupons"
        )

    try:

        return service.create_coupon(payload)

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "coupon_create_server_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create coupon"
        )

# ======================================================
# APPLY COUPON
# ======================================================

@router.post(
    "/apply",
    response_model=ApplyCouponResponse,
    summary="Apply coupon to cart"
)
def apply_coupon(
    payload: ApplyCouponRequest,
    service: CouponService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Apply coupon to order/cart.

    Returns:
    • Discount amount
    • Final payable amount
    """

    try:

        return service.apply_coupon(
            user_id=current_user["user_id"],
            code=payload.code,
            order_amount=payload.order_amount
        )

    except ValueError as e:

        log_event(
            "coupon_apply_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            code=payload.code,
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "coupon_apply_server_error",
            level="critical",
            user_id=current_user["user_id"],
            code=payload.code,
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply coupon"
        )


# ======================================================
# VALIDATE COUPON (LIGHTWEIGHT)
# ======================================================

@router.post(
    "/validate",
    response_model=ValidateCouponResponse,
    summary="Validate coupon"
)
def validate_coupon(
    payload: ApplyCouponRequest,
    service: CouponService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Validate coupon without applying.

    Useful for:
    • Instant UI feedback
    """

    try:

        service.validate_coupon(
            user_id=current_user["user_id"],
            code=payload.code,
            order_amount=payload.order_amount
        )

        return {
            "is_valid": True,
            "message": "Coupon is valid"
        }

    except ValueError as e:

        return {
            "is_valid": False,
            "message": str(e)
        }

    except Exception as e:

        log_event(
            "coupon_validate_error",
            level="error",
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation failed"
        )


# ======================================================
# CONFIRM USAGE (INTERNAL - OPTIONAL)
# ======================================================

@router.post(
    "/confirm",
    response_model=MessageResponse,
    summary="Confirm coupon usage (internal)"
)
def confirm_coupon_usage(
    coupon_id: int,
    order_id: int,
    service: CouponService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Confirm coupon usage AFTER successful order.

    ⚠️ Typically called internally (not frontend).
    """

    try:

        service.confirm_coupon_usage(
            user_id=current_user["user_id"],
            coupon_id=coupon_id,
            order_id=order_id
        )

        return {"message": "Coupon usage recorded"}

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "coupon_confirm_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm coupon usage"
        )