"""
Search Schemas

Defines request validation and response models
for product search APIs.

Responsibilities
----------------
• Validate search query parameters
• Standardize search responses
• Support pagination

Architecture
------------
Client → API Schema → Service → Repository
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal


# =========================================================
# SEARCH QUERY PARAMETERS
# =========================================================

class ProductSearchQuery(BaseModel):
    """
    Query parameters for product search.
    """

    q: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Keyword search"
    )

    brand_id: Optional[int] = Field(
        default=None,
        description="Filter by brand"
    )

    category_id: Optional[int] = Field(
        default=None,
        description="Filter by category"
    )

    min_price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Minimum price filter"
    )

    max_price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Maximum price filter"
    )

    sort_by: Optional[str] = Field(
        default=None,
        description="Sorting option: price_asc, price_desc, newest"
    )

    page: int = Field(
        default=1,
        ge=1,
        description="Page number"
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page"
    )   


# =========================================================
# SEARCH RESULT ITEM
# =========================================================

class SearchProductItem(BaseModel):
    """
    Product representation in search results.
    """

    id: int
    name: str
    slug: str

    price: Decimal
    compare_price: Optional[Decimal]

    brand_id: Optional[int]
    category_id: Optional[int]

    is_active: bool

    primary_image: Optional[str] = None


# =========================================================
# SEARCH RESPONSE
# =========================================================

class ProductSearchResponse(BaseModel):
    """
    Paginated product search response.
    """

    total: int
    page: int
    limit: int

    items: List[SearchProductItem]