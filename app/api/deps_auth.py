"""
Authentication Dependencies

Provides:
- get_current_user()

Used by:
- protected routes
- RBAC permissions
- admin/vendor/customer APIs
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.user import AccountStatus

from app.core.security import verify_access_token
from app.core.logger import log_event
from app.api.deps import get_db
from app.models.user import User

# --------------------------------------------------
# BEARER SECURITY SCHEME
# --------------------------------------------------

security = HTTPBearer(auto_error=False)


# --------------------------------------------------
# GET CURRENT USER
# --------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Extract and verify JWT access token.

    Returns normalized user payload:
    {
        "user_id": int,
        "role": str,
        "status": str
    }
    """

    try:

        # --------------------------------------------------
        # CHECK AUTH HEADER
        # --------------------------------------------------

        if credentials is None:

            log_event(
                "auth_header_missing",
                level="warning"
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        token = credentials.credentials

        if not token:

            log_event(
                "auth_token_missing",
                level="warning"
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token missing"
            )

        # --------------------------------------------------
        # VERIFY TOKEN
        # --------------------------------------------------

        payload = verify_access_token(token)

        if not isinstance(payload, dict):

            log_event(
                "auth_payload_not_dict",
                level="warning"
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        user_id = payload.get("sub")
        role = payload.get("role")

        if user_id is None or role is None:

            log_event(
                "auth_payload_invalid",
                level="warning",
                payload=payload
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):

            log_event(
                "auth_user_id_invalid",
                level="warning",
                user_id=user_id
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        # --------------------------------------------------
        # LOAD USER FROM DATABASE
        # --------------------------------------------------

        user = db.query(User).filter(User.id == user_id).first()

        if not user:

            log_event(
                "auth_user_not_found",
                level="warning",
                user_id=user_id
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # --------------------------------------------------
        # ACCOUNT STATUS CHECK
        # --------------------------------------------------

        if user.status != AccountStatus.ACTIVE:

            log_event(
                "account_access_blocked",
                level="warning",
                user_id=user.id,
                account_status=str(user.status)
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )

        # --------------------------------------------------
        # NORMALIZED USER OBJECT
        # --------------------------------------------------

        user_data: Dict[str, Any] = {
            "user_id": user.id,
            "role": user.role.value,
            "status": user.status.value
        }

        return user_data


    except ValueError as e:

        log_event(
            "auth_token_invalid",
            level="warning",
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    except HTTPException:
        raise

    except Exception as e:

        log_event(
            "auth_dependency_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )