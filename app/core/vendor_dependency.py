from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.models.vendor_profile import VendorProfile


def get_current_vendor(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if user["role"] != "vendor":
        raise HTTPException(status_code=403, detail="Vendor access required")

    vendor = (
        db.query(VendorProfile)
        .filter(VendorProfile.user_id == user["user_id"])
        .first()
    )

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor profile not found")

    if not vendor.verification_status:
        raise HTTPException(
            status_code=403,
            detail="Vendor not approved yet"
        )

    return vendor