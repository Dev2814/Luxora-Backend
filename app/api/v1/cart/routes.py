"""
Cart Routes
===========

API endpoints responsible for customer cart management.

Responsibilities
----------------
• Add item to cart
• Retrieve cart items
• Update cart quantity
• Remove item from cart
• Clear cart

Role Access
-----------
Customer
    • POST   /cart/add
    • GET    /cart
    • PUT    /cart/update
    • DELETE /cart/remove/{variant_id}
    • DELETE /cart/clear

Architecture
------------
Routes → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.core.logger import log_event

from app.domains.cart.service import CartService

from app.api.v1.cart.schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse
)

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)

# ======================================================
# SERVICE DEPENDENCY
# ======================================================

def get_cart_service(db: Session = Depends(get_db)) -> CartService:
    return CartService(db)


# ======================================================
# GET CART
# ======================================================

@router.get(
    "/",
    response_model=CartResponse,
    summary="Get Customer Cart"
)
def get_cart(
    service: CartService = Depends(get_cart_service),
    current_user=Depends(get_current_user)
):

    try:

        items = service.get_cart_items(current_user["user_id"])

        return {"items": items}

    except Exception as e:

        log_event(
            "cart_fetch_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch cart"
        )


# ======================================================
# ADD ITEM TO CART
# ======================================================

@router.post(
    "/add",
    summary="Add Item to Cart"
)
def add_item(
    payload: CartItemCreate,
    service: CartService = Depends(get_cart_service),
    current_user=Depends(get_current_user)
):

    try:

        return service.add_item(
            user_id=current_user["user_id"],
            variant_id=payload.variant_id,
            quantity=payload.quantity
        )

    except ValueError as e:

        log_event(
            "cart_add_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        log_event(
            "cart_add_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to add item to cart"
        )


# ======================================================
# UPDATE ITEM QUANTITY
# ======================================================

@router.put(
    "/update",
    summary="Update Cart Item Quantity"
)
def update_item(
    payload: CartItemUpdate,
    service: CartService = Depends(get_cart_service),
    current_user=Depends(get_current_user)
):

    try:

        return service.update_item(
            user_id=current_user["user_id"],
            variant_id=payload.variant_id,
            quantity=payload.quantity
        )

    except ValueError as e:

        log_event(
            "cart_update_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        log_event(
            "cart_update_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to update cart item"
        )


# ======================================================
# REMOVE ITEM FROM CART
# ======================================================

@router.delete(
    "/item/{item_id}",
    summary="Remove Item From Cart"
)
def remove_item(
    item_id: int,
    service: CartService = Depends(get_cart_service),
    current_user=Depends(get_current_user)
):

    try:

        service.remove_item_by_id(
            user_id=current_user["user_id"],
            item_id=item_id
        )

        return {"message": "Item removed from cart"}

    except ValueError as e:

        log_event(
            "cart_remove_validation_error",
            level="warning",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        log_event(
            "cart_remove_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to remove cart item"
        )

# ======================================================
# CLEAR CART
# ======================================================

@router.delete(
    "/clear",
    summary="Clear Cart"
)
def clear_cart(
    service: CartService = Depends(get_cart_service),
    current_user=Depends(get_current_user)
):

    try:

        service.clear_cart(current_user["user_id"])

        return {"message": "Cart cleared successfully"}

    except Exception as e:

        log_event(
            "cart_clear_server_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to clear cart"
        )