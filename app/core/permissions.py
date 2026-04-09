"""
RBAC Permission System
======================

Provides role-based access control for Luxora backend.

Features
--------
• Role validation
• Multi-role authorization
• Verified vendor enforcement
• Account status validation
• Security logging
• Custom role-based error messages

Architecture
------------
API → Permission Guard → Business Logic
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps_auth import get_current_user
from app.api.deps import get_db
from app.core.logger import log_event

from app.models.vendor_profile import VendorProfile
from app.models.user import AccountStatus

# ======================================================
# INTERNAL ACCOUNT STATUS VALIDATION
# ======================================================

def _validate_account_status(user: dict):
    """
    Internal security guard that ensures the user account
    is active before allowing any API access.
    """

    status_value = user.get("status")

    if status_value != AccountStatus.ACTIVE:

        log_event(
            "account_access_blocked",
            level="warning",
            user_id=user.get("user_id"),
            account_status=str(status_value)
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )

# ======================================================
# SINGLE ROLE CHECK
# ======================================================

def require_role(required_role: str):
    """
    Restricts API access to a single role.

    Example
    -------
    dependencies=[Depends(require_role("admin"))]
    """

    required = required_role.lower()

    def role_checker(user=Depends(get_current_user)):

        # Validate account status first
        _validate_account_status(user)

        user_role = str(user.get("role", "")).lower()

        # --------------------------------------------------
        # SUPER ADMIN OVERRIDE
        # --------------------------------------------------

        if user_role == "super_admin":
            return user

        # --------------------------------------------------
        # ROLE VALIDATION
        # --------------------------------------------------

        if user_role != required:

            log_event(
                "rbac_forbidden_access",
                level="warning",
                user_id=user.get("user_id"),
                required_role=required,
                user_role=user_role
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You are not able to use this service. Only {required} can access it."
            )

        return user

    return role_checker

# ======================================================
# MULTIPLE ROLE CHECK
# ======================================================

def require_roles(*roles: str):
    """
    Restricts API access to multiple roles.

    Example
    -------
    dependencies=[Depends(require_roles("admin","support"))]
    """

    allowed_roles: List[str] = [r.lower() for r in roles]

    def role_checker(user=Depends(get_current_user)):

        # Validate account status
        _validate_account_status(user)

        user_role = str(user.get("role", "")).lower()

        # --------------------------------------------------
        # SUPER ADMIN OVERRIDE
        # --------------------------------------------------

        if user_role == "super_admin":
            return user

        # --------------------------------------------------
        # ROLE VALIDATION
        # --------------------------------------------------

        if user_role not in allowed_roles:

            log_event(
                "rbac_multiple_role_denied",
                level="warning",
                user_id=user.get("user_id"),
                allowed_roles=allowed_roles,
                user_role=user_role
            )

            allowed = ", ".join(allowed_roles)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You are not able to use this service. Only {allowed} can access it."
            )

        return user

    return role_checker

# ======================================================
# VERIFIED VENDOR CHECK
# ======================================================

def require_verified_vendor():
    """
    Ensures the user is a verified vendor before accessing
    vendor-specific APIs.

    Validation Steps
    ----------------
    1. User must have vendor role
    2. Vendor profile must exist
    3. Vendor must be approved by admin
    """

    def checker(
        user=Depends(get_current_user),
        db: Session = Depends(get_db)
    ):

        # Validate account status first
        _validate_account_status(user)

        user_role = str(user.get("role", "")).lower()

        # --------------------------------------------------
        # ROLE VALIDATION
        # --------------------------------------------------

        if user_role != "vendor":

            log_event(
                "non_vendor_access_attempt",
                level="warning",
                user_id=user.get("user_id")
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not able to use this service. Only verified vendors can access it."
            )

        # --------------------------------------------------
        # FETCH VENDOR PROFILE
        # --------------------------------------------------

        vendor = (
            db.query(VendorProfile)
            .filter(VendorProfile.user_id == user["user_id"])
            .one_or_none()
        )

        if not vendor:

            log_event(
                "vendor_profile_missing",
                level="warning",
                user_id=user.get("user_id")
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vendor profile not found"
            )

        # --------------------------------------------------
        # VENDOR APPROVAL STATUS
        # --------------------------------------------------

        if not vendor.verification_status:

            if vendor.rejection_reason:

                log_event(
                    "vendor_access_rejected",
                    level="warning",
                    user_id=user.get("user_id"),
                    reason=vendor.rejection_reason
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your vendor application was rejected by admin"
                )

            log_event(
                "vendor_access_pending",
                level="warning",
                user_id=user.get("user_id")
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your vendor approval is pending"
            )

        return user

    return checker