"""
Vendor Analytics Routes
======================

Provides vendor dashboard metrics.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.core.permissions import require_role

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


@router.get(
    "/dashboard",
    response_model=VendorDashboardResponse,
    summary="Vendor Dashboard Analytics"
)
def get_dashboard(
    service: VendorAnalyticsService = Depends(get_service),
    current_user=Depends(get_current_user)
):
    try:
        vendor_id = current_user["user_id"]

        return service.get_dashboard(vendor_id)

    except Exception as e:

        log_event(
            "vendor_dashboard_error",
            level="critical",
            error=str(e),
            user_id=current_user.get("user_id")
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch dashboard data"
        )