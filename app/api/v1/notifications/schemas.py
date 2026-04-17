"""
Notification Schemas
====================

Pydantic schemas for the notifications API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# =========================================================
# FCM TOKEN REGISTRATION
# =========================================================

class FCMTokenRegister(BaseModel):
    """
    Payload for registering a vendor's device FCM token.
    """

    fcm_token: str = Field(
        ...,
        min_length=10,
        description="Firebase Cloud Messaging device registration token"
    )


# =========================================================
# NOTIFICATION RESPONSE
# =========================================================

class NotificationResponse(BaseModel):
    """
    Single notification item response.
    """

    id: int
    title: str
    message: str
    is_read: bool
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =========================================================
# NOTIFICATION LIST RESPONSE
# =========================================================

class NotificationListResponse(BaseModel):
    """
    Paginated list of notifications.
    """

    total: int
    unread_count: int
    items: List[NotificationResponse]
