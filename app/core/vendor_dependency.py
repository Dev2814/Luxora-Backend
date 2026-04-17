"""
Vendor Dependency
=================

Provides authenticated and validated vendor context.

Responsibilities:
-----------------
• Ensure user is authenticated
• Ensure user has vendor role
• Fetch vendor profile from database
• Validate vendor approval status

Usage:
------
Inject into routes that require vendor access:

    vendor = Depends(get_current_vendor)

Architecture:
-------------
Route → Dependency → Database → VendorProfile
"""

# =========================================================
# IMPORTS
# =========================================================

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user

from app.models.vendor_profile import VendorProfile


# =========================================================
# DEPENDENCY: GET CURRENT VENDOR
# =========================================================

def get_current_vendor(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve and validate the current vendor.

    Validations:
    ------------
    • User must have role = 'vendor'
    • Vendor profile must exist
    • Vendor must be approved (verification_status)

    Returns:
    --------
    VendorProfile
        Authenticated and validated vendor object
    """

    # --------------------------------------------------
    # ROLE VALIDATION
    # --------------------------------------------------

    if user["role"] != "vendor":
        raise HTTPException(
            status_code=403,
            detail="Vendor access required"
        )

    # --------------------------------------------------
    # FETCH VENDOR PROFILE
    # --------------------------------------------------

    vendor = (
        db.query(VendorProfile)
        .filter(VendorProfile.user_id == user["user_id"])
        .first()
    )

    if not vendor:
        raise HTTPException(
            status_code=404,
            detail="Vendor profile not found"
        )

    # --------------------------------------------------
    # VERIFICATION CHECK
    # --------------------------------------------------

    if not vendor.verification_status:
        raise HTTPException(
            status_code=403,
            detail="Vendor not approved yet"
        )

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------

    return vendor