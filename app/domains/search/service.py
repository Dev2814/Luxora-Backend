"""
Search Service

Handles product search business logic.

Responsibilities
----------------
• Process product search requests
• Validate search parameters
• Call repository for database queries
• Format paginated responses
• Log search events

Architecture
------------
API Route → Service → Repository → Database
"""

from sqlalchemy.orm import Session

from app.domains.search.repository import SearchRepository
from app.core.logger import log_event


class SearchService:
    """
    Service responsible for handling product search logic.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = SearchRepository(db)

    # =========================================================
    # SEARCH PRODUCTS
    # =========================================================

    def search_products(
        self,
        keyword: str | None = None,
        brand_id: int | None = None,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort_by: str | None = None,
        page: int = 1,
        limit: int = 20,
    ):
        """
        Search products with filters and pagination.
        """

        total, items = self.repository.search_products(
            keyword=keyword,
            brand_id=brand_id,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            page=page,
            limit=limit,
        )

        # -----------------------------------------------------
        # LOG SEARCH EVENT
        # -----------------------------------------------------

        log_event(
            "product_search",
            keyword=keyword,
            brand_id=brand_id,
            category_id=category_id,
            page=page,
            limit=limit,
            results=total,
        )

        # -----------------------------------------------------
        # RETURN PAGINATED RESPONSE
        # -----------------------------------------------------

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": items
        }