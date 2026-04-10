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

from app.domains.orders.service import OrderService
from app.domains.orders.repository import OrderRepository

from app.api.v1.orders.schemas import (
    CheckoutRequest,
    OrderResponse
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