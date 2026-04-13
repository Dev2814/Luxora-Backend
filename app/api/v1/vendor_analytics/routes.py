"""
Vendor Analytics Routes
======================

Provides vendor dashboard metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.core.permissions import require_role
from app.models.vendor_profile import VendorProfile
from app.api.v1.vendor_analytics.schemas import (
    VendorDashboardResponse, 
    RevenueChartResponse,
    LowStockResponse,
    VendorEarningsResponse,
    VendorProductOrdersResponse
)

from app.domains.vendor_analytics.service import VendorAnalyticsService
from app.api.v1.vendor_analytics.schemas import VendorDashboardResponse

from app.core.logger import log_event


router = APIRouter(
    prefix="/vendor/analytics",
    tags=["Vendor Analytics"],
    dependencies=[Depends(require_role("vendor"))]
)


def get_service(db: Session = Depends(get_db)):
    return VendorAnalyticsService(db)


# =========================================================
# DASHBOARD ENDPOINT
# =========================================================

@router.get(
    "/dashboard",
    response_model=VendorDashboardResponse,
    dependencies=[Depends(require_role("vendor"))],
    summary="Get Vendor Dashboard"
)
def get_dashboard(
    service: VendorAnalyticsService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Fetch vendor dashboard summary.

    Includes:
    • Products count
    • Orders count
    • Revenue
    • Low stock alerts
    """

    try:
        db = service.repo.db
        # 🔹 Fetch vendor profile using user_id
        vendor = db.query(VendorProfile).filter(
            VendorProfile.user_id == current_user["user_id"]
        ).first()

        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor profile not found")

        # 🔹 Pass correct vendor_id
        return service.get_dashboard(
            vendor_id=vendor.id
        )

    except Exception as e:
        
        log_event(
            "vendor_dashboard_error",
            level="critical",
            user_id=current_user["user_id"],
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch dashboard"
        )
    
@router.get(
    "/revenue-chart",
    response_model=RevenueChartResponse,
    dependencies=[Depends(require_role("vendor"))],
)
def get_revenue_chart(
    range: str = Query("7d"),
    service: VendorAnalyticsService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    # 🔹 convert range → days
    days_map = {
        "7d": 7,
        "30d": 30,
        "90d": 90
    }

    days = days_map.get(range, 7)

    # 🔹 get vendor_id (same fix as dashboard)
    db = service.repo.db
    from app.models.vendor_profile import VendorProfile

    vendor = db.query(VendorProfile).filter(
        VendorProfile.user_id == current_user["user_id"]
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return service.get_revenue_chart(vendor.id, days)

@router.get(
    "/low-stock",
    response_model=LowStockResponse,
    dependencies=[Depends(require_role("vendor"))],
    summary="Get Low Stock Products"
)
def get_low_stock(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    service: VendorAnalyticsService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Get products/variants with low stock.

    Uses:
    - Inventory threshold logic
    - Vendor filtering
    """

    db = service.repo.db
    from app.models.vendor_profile import VendorProfile

    vendor = db.query(VendorProfile).filter(
        VendorProfile.user_id == current_user["user_id"]
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return service.get_low_stock(
        vendor.id,
        page,
        limit
    )

# =========================================================
# VENDOR EARNINGS ENDPOINT
# =========================================================

@router.get(
    "/earnings",
    response_model=VendorEarningsResponse,
    dependencies=[Depends(require_role("vendor"))],
    summary="Get Vendor Earnings"
)
def get_earnings(
    service: VendorAnalyticsService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    """
    Get vendor earnings summary.
    """

    db = service.repo.db
    from app.models.vendor_profile import VendorProfile

    vendor = db.query(VendorProfile).filter(
        VendorProfile.user_id == current_user["user_id"]
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return service.get_earnings(vendor.id)

# =========================================================
# VENDOR PRODUCT ORDERS ENDPOINT
# =========================================================
@router.get(
    "/product-orders",
    response_model=VendorProductOrdersResponse,
    summary="Get Vendor Product Orders"
)
def get_product_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    service: VendorAnalyticsService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    db = service.repo.db

    vendor = db.query(VendorProfile).filter(
        VendorProfile.user_id == current_user["user_id"]
    ).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return service.get_product_orders(
        vendor.id,
        page,
        limit
    )