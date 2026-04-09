"""
Vendor Analytics Schemas
=======================

Defines response models for vendor dashboard analytics.

Used by:
- Vendor dashboard UI
"""

from pydantic import BaseModel
from typing import List


class RevenuePoint(BaseModel):
    date: str
    revenue: float


class VendorDashboardResponse(BaseModel):
    total_orders: int
    pending_orders: int
    total_sales: float
    revenue_chart: List[RevenuePoint]