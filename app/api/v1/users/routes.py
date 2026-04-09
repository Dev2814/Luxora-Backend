"""
User Routes
===========

Handles user profile related APIs.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.api.deps_auth import get_current_user

from app.domains.users.service import UserService
from app.api.v1.users.schemas import (
    UserProfileResponse,
    UpdateProfileRequest,
    SessionResponse
)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# =====================================================
# GET PROFILE
# =====================================================

@router.get("/me", response_model=UserProfileResponse)
def get_profile(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.get_profile(current_user["user_id"])


# =====================================================
# UPDATE PROFILE
# =====================================================

@router.put("/me")
def update_profile(
    payload: UpdateProfileRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UserService(db)

    return service.update_profile(
        current_user["user_id"],
        payload
    )


# =====================================================
# GET ACTIVE SESSIONS
# =====================================================

@router.get("/sessions", response_model=list[SessionResponse])
def get_sessions(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.get_sessions(current_user["user_id"])


# =====================================================
# REVOKE SESSION
# =====================================================

@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.revoke_session(session_id)