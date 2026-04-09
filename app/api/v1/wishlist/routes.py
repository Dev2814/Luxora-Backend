"""
Wishlist Routes
===============

Enterprise-grade wishlist API.

Features
--------
• Authenticated access only
• Clean response structure
• Consistent with order system
• Proper error handling
• Production-ready API design
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user

from app.domains.Wishlist.service import WishlistService
from app.api.v1.wishlist.schemas import (
    WishlistAddRequest,
    WishlistResponse,
    MessageResponse
)

router = APIRouter(
    prefix="/wishlist",
    tags=["Wishlist"]
)

# ======================================================
# DEPENDENCY
# ======================================================

def get_service(db: Session = Depends(get_db)) -> WishlistService:
    return WishlistService(db)

# ======================================================
# ADD ITEM
# ======================================================

@router.post(
    "/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to wishlist"
)
def add_to_wishlist(
    payload: WishlistAddRequest,
    service: WishlistService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Add a product variant to the authenticated user's wishlist.

    Rules:
    • User must be authenticated
    • Prevent duplicate entries
    """

    try:

        return service.add_to_wishlist(
            user_id=current_user["user_id"],
            variant_id=payload.variant_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ======================================================
# REMOVE ITEM
# ======================================================

@router.delete(
    "/{variant_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove item from wishlist"
)
def remove_from_wishlist(
    variant_id: int,
    service: WishlistService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Remove a product from wishlist.
    """

    try:

        return service.remove_from_wishlist(
            user_id=current_user["user_id"],
            variant_id=variant_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ======================================================
# GET WISHLIST
# ======================================================

@router.get(
    "/",
    response_model=WishlistResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user wishlist"
)
def get_wishlist(
    service: WishlistService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Retrieve full wishlist with enriched product data.

    Includes:
    • Product name
    • Price
    • Image
    • Stock status
    """

    try:

        # ✅ FIX: service already returns correct structure
        return service.get_wishlist(current_user["user_id"])

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )