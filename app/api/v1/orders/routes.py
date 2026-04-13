"""
Order Routes
============

API endpoints responsible for checkout and order management.

Responsibilities
----------------
• Checkout (create order from cart)
• Retrieve user orders
• Retrieve single order

Role Access
-----------
Customer
    • POST   /orders/checkout
    • GET    /orders
    • GET    /orders/{id}

Architecture
------------
Routes → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.core.logger import log_event
from app.models.vendor_profile import VendorProfile

from app.domains.orders.service import OrderService
from app.domains.orders.repository import OrderRepository

from app.api.v1.orders.schemas import (
    CheckoutRequest,
    OrderResponse,
    UpdateOrderStatusRequest,
    VendorOrderDetailsResponse,
    VendorOrderListResponse,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

# ======================================================
# SERVICE DEPENDENCY
# ======================================================

def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(db)


def get_order_repository(db: Session = Depends(get_db)) -> OrderRepository:
    return OrderRepository(db)


# ======================================================
# CHECKOUT
# ======================================================

@router.post(
    "/checkout",
    response_model=OrderResponse,
    summary="Checkout Cart and Create Order"
)
def checkout(
    payload: CheckoutRequest,
    service: OrderService = Depends(get_order_service),
    current_user=Depends(get_current_user)
):

    try:

        return service.checkout(
            user_id=current_user["user_id"],
            address_id=payload.address_id
        )

    except ValueError as e:

        log_event(
            "checkout_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        log_event(
            "checkout_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Checkout failed"
        )


# ======================================================
# LIST USER ORDERS
# ======================================================

@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="Get User Orders"
)
def list_orders(
    repo: OrderRepository = Depends(get_order_repository),
    service: OrderService = Depends(get_order_service),
    current_user=Depends(get_current_user)
):

    try:

       return service.get_orders(current_user["user_id"])

    except Exception as e:

        log_event(
            "order_list_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch orders"
        )


# ======================================================
# VENDOR ORDER LIST
# ======================================================

@router.get(
    "/vendor",
    response_model=VendorOrderListResponse,
    summary="Get Vendor Orders",
    description="Fetch all orders for the vendor"
)
def get_vendor_orders(
    service: OrderService = Depends(get_order_service),
    current_user=Depends(get_current_user)
):
    try:
        # -------------------------------
        # ROLE CHECK
        # -------------------------------
        if current_user["role"] != "vendor":
            raise HTTPException(status_code=403, detail="Only vendors allowed")

        # -------------------------------
        # GET VENDOR PROFILE
        # -------------------------------
        vendor = service.db.query(VendorProfile).filter(
            VendorProfile.user_id == current_user["user_id"]
        ).first()

        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        # -------------------------------
        # FETCH ORDERS
        # -------------------------------
        return service.get_vendor_orders(vendor.id)

    except Exception as e:
        log_event(
            "vendor_order_list_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch vendor orders"
        )


# ======================================================
# GET ORDER BY ID
# ======================================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get Order Details"
)
def get_order(
    order_id: int,
    repo: OrderRepository = Depends(get_order_repository),
    current_user=Depends(get_current_user)
):

    try:

        order = repo.get_order_by_id(order_id)

        if not order or order.user_id != current_user["user_id"]:
            raise HTTPException(status_code=404, detail="Order not found")
        
        service = OrderService(repo.db)

        return service.get_single_order(order_id)

    except HTTPException:
        raise

    except Exception as e:

        log_event(
            "order_fetch_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch order"
        )

# ======================================================
# VENDOR ORDER DETAILS
# ======================================================

@router.get(
    "/vendor/{order_id}",
    response_model=VendorOrderDetailsResponse,
    summary="Get Vendor Order Details",
    description="Fetch full order details for a vendor including customer info and items"
)
def get_vendor_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
    current_user=Depends(get_current_user)
):

    try:
        # --------------------------------------------------
        # ROLE-BASED ACCESS CONTROL (RBAC)
        # --------------------------------------------------
        if current_user["role"] != "vendor":
            raise HTTPException(
                status_code=403,
                detail="Access denied. Vendor role required."
            )

        # -------------------------------
        # FIX: USER → VENDOR PROFILE
        # -------------------------------
        vendor = service.db.query(VendorProfile).filter(
            VendorProfile.user_id == current_user["user_id"]
        ).first()

        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # --------------------------------------------------
        # FETCH ORDER DETAILS
        # --------------------------------------------------

        return service.get_vendor_order_details(
            vendor.id,  # vendor_id
            order_id
        )

    except ValueError as e:
        # --------------------------------------------------
        # BUSINESS LOGIC ERROR
        # --------------------------------------------------
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        # --------------------------------------------------
        # UNEXPECTED ERROR (LOGGING)
        # --------------------------------------------------
        log_event(
            "vendor_order_fetch_error",
            level="critical",
            order_id=order_id,
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch vendor order"
        )

# ======================================================
# UPDATE ORDER STATUS (VENDOR)
# ======================================================

@router.patch(
    "/vendor/{order_id}/status",
    summary="Update Order Status",
    description="Allows vendor to update order status with validation"
)
def update_order_status(
    order_id: int,
    payload: UpdateOrderStatusRequest,
    service: OrderService = Depends(get_order_service),
    current_user=Depends(get_current_user)
):
    try:
        # --------------------------------------------------
        # ROLE-BASED ACCESS CONTROL (RBAC)
        # --------------------------------------------------
        if current_user["role"] != "vendor":
            raise HTTPException(
                status_code=403,
                detail="Access denied. Vendor role required."
            )
        
        # -------------------------------
        # FIX: USER → VENDOR PROFILE
        # -------------------------------
        vendor = service.db.query(VendorProfile).filter(
            VendorProfile.user_id == current_user["user_id"]
        ).first()

        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        # --------------------------------------------------
        # UPDATE ORDER STATUS
        # --------------------------------------------------
        return service.update_order_status(
            vendor.id,  # vendor_id
            order_id,
            payload.status
        )

    except ValueError as e:
        # --------------------------------------------------
        # VALIDATION OR BUSINESS ERROR
        # --------------------------------------------------
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # --------------------------------------------------
        # UNEXPECTED ERROR (LOGGING)
        # --------------------------------------------------
        log_event(
            "vendor_order_status_update_error",
            level="critical",
            order_id=order_id,
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to update order status"
        )   
   