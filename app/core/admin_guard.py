"""
Admin Authorization Guard
Ensures only admin users access admin endpoints.
"""

from fastapi import Depends, HTTPException, status

from app.api.deps_auth import get_current_user
from app.core.logger import log_event


def require_admin(user=Depends(get_current_user)):

    try:

        if user["role"] != "admin":

            log_event(
                "admin_access_denied",
                level="warning",
                user_id=user["user_id"]
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        return user

    except HTTPException:
        raise

    except Exception as e:

        log_event(
            "admin_guard_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization failed"
        )