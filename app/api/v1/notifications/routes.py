"""
Notification Routes
===================

API endpoints for managing vendor push notifications.

Endpoints:
----------
• POST /notifications/fcm-token     → Register/update vendor FCM device token
• GET  /notifications/              → Get all my notifications (vendor)
• PATCH /notifications/{id}/read   → Mark single notification as read
• PATCH /notifications/read-all    → Mark all notifications as read

Architecture:
-------------
Flutter Vendor App → POST /fcm-token → Store in vendor_profiles.fcm_token
Customer Order     → FCM Push → Flutter App receives notification
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.api.deps_auth import get_current_user
from app.core.permissions import require_role
from app.core.logger import log_event

from app.models.notification import Notification
from app.models.vendor_profile import VendorProfile

from app.api.v1.notifications.schemas import (
    FCMTokenRegister,
    NotificationResponse,
    NotificationListResponse
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# =========================================================
# REGISTER FCM TOKEN
# =========================================================

@router.post(
    "/fcm-token",
    summary="Register vendor FCM device token",
    dependencies=[Depends(require_role("vendor"))]
)
def register_fcm_token(
    payload: FCMTokenRegister,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Called by the Flutter vendor app on startup or when Firebase
    refreshes the registration token.

    Stores the token in vendor_profiles.fcm_token so the backend
    can send push notifications when new orders arrive.
    """

    vendor = (
        db.query(VendorProfile)
        .filter(VendorProfile.user_id == user["user_id"])
        .first()
    )

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor profile not found")

    vendor.fcm_token = payload.fcm_token

    db.commit()

    log_event(
        "vendor_fcm_token_registered",
        user_id=user["user_id"],
        vendor_id=vendor.id
    )

    return {"message": "FCM token registered successfully"}


# =========================================================
# GET MY NOTIFICATIONS
# =========================================================

@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="Get vendor notifications",
    dependencies=[Depends(require_role("vendor"))]
)
def get_notifications(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all notifications for the authenticated vendor,
    ordered by latest first.

    Also returns total count and unread count for badge display.
    """

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user["user_id"])
        .order_by(Notification.created_at.desc())
        .all()
    )

    unread_count = sum(1 for n in notifications if not n.is_read)

    return NotificationListResponse(
        total=len(notifications),
        unread_count=unread_count,
        items=notifications
    )


# =========================================================
# MARK SINGLE NOTIFICATION AS READ
# =========================================================

@router.patch(
    "/{notification_id}/read",
    summary="Mark a notification as read",
    dependencies=[Depends(require_role("vendor"))]
)
def mark_notification_read(
    notification_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a single notification as read.

    Validates that the notification belongs to the authenticated vendor.
    """

    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user["user_id"]
        )
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read", "id": notification_id}


# =========================================================
# MARK ALL NOTIFICATIONS AS READ
# =========================================================

@router.patch(
    "/read-all",
    summary="Mark all notifications as read",
    dependencies=[Depends(require_role("vendor"))]
)
def mark_all_notifications_read(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all unread notifications as read for the vendor.

    Used when the vendor opens the notifications screen.
    """

    updated = (
        db.query(Notification)
        .filter(
            Notification.user_id == user["user_id"],
            Notification.is_read == False
        )
        .update({"is_read": True})
    )

    db.commit()

    log_event(
        "vendor_notifications_all_read",
        user_id=user["user_id"],
        count=updated
    )

    return {"message": "All notifications marked as read", "updated": updated}
