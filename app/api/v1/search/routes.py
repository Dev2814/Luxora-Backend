"""
Search Routes

API endpoints for product search.

Responsibilities
----------------
• Product keyword search
• Filtering by brand, category, price
• Sorting
• Pagination

Architecture
------------
Route → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal

from app.api.deps import get_db

from app.domains.search.service import SearchService

from app.api.v1.search.schemas import ProductSearchResponse


router = APIRouter(
    prefix="/search",
    tags=["Search"]
)

# =========================================================
# PRODUCT SEARCH
# =========================================================

@router.get(
    "/products",
    response_model=ProductSearchResponse,
    summary="Search Products"
)
def search_products(
    q: Optional[str] = Query(default=None, min_length=1),
    brand_id: Optional[int] = Query(default=None),
    category_id: Optional[int] = Query(default=None),
    min_price: Optional[Decimal] = Query(default=None, ge=0),
    max_price: Optional[Decimal] = Query(default=None, ge=0),
    sort_by: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search products with filters.

    Supports:
    - keyword search
    - brand filtering
    - category filtering
    - price filtering
    - sorting
    - pagination
    """

    service = SearchService(db)

    try:

        return service.search_products(
            keyword=q,
            brand_id=brand_id,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            page=page,
            limit=limit
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )