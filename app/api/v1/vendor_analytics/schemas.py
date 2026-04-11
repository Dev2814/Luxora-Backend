"""
Vendor Analytics Schemas
=======================

Defines response models for vendor dashboard analytics.

Used by:
- Vendor dashboard UI
"""

from pydantic import BaseModel
from typing import List

# ======================================================
# VENDOR DASHBOARD RESPONSE
# ======================================================


class RevenuePoint(BaseModel):
    date: str
    revenue: float


class RevenueChartResponse(BaseModel):
    data: list[RevenuePoint]

class VendorDashboardResponse(BaseModel):
    """
    Aggregated dashboard response for vendor.
    """

    total_products: int
    total_orders: int
    total_revenue: float
    low_stock_count: int

# ======================================================
# LOW STOCK ALERT RESPONSE
# ======================================================


class LowStockItem(BaseModel):
    product_id: int
    product_name: str
    variant_id: int
    variant_name: str
    stock: int
    threshold: int


class LowStockResponse(BaseModel):
    items: List[LowStockItem]
    total: int
    page: int
    limit: int

# ======================================================
# VENDOR EARNINGS RESPONSE
# ======================================================

class VendorEarningsResponse(BaseModel):
    total_revenue: float
    total_orders: int
    paid_revenue: float
    pending_revenue: float