"""
Auth Routes

Handles authentication endpoints.

Architecture:
Route → Service → Repository → Database
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps_auth import get_current_user

from app.domains.auth.service import AuthService
from app.domains.auth.login_history_service import LoginHistoryService

from app.models.user import User

from app.api.v1.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    OTPVerifyRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    RefreshRequest,
    ResendOTPRequest
)

from app.core.logger import log_event

from app.core.rate_limiter import (
    login_rate_limiter,
    otp_verify_rate_limiter,
    otp_resend_rate_limiter,
    api_rate_limiter
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==========================================================
# UTILITIES
# ==========================================================

def get_client_ip(request: Request) -> str:

    forwarded = request.headers.get("x-forwarded-for")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


# ==========================================================
# SERVICE DEPENDENCY
# ==========================================================

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


# ==========================================================
# REGISTER
# ==========================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(api_rate_limiter)]
)
def register_user(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service)
):

    try:
        return service.register_user(payload)

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "register_route_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )


# ==========================================================
# LOGIN STEP 1
# ==========================================================

@router.post(
    "/login",
    dependencies=[Depends(login_rate_limiter)]
)
def login_user(
    payload: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service)
):

    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")

    try:

        return service.login_password_step(
            payload.email,
            payload.password,
            ip,
            user_agent
        )

    except ValueError as e:

        log_event(
            "login_failed",
            level="warning",
            email=payload.email,
            ip=ip
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "login_route_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )


# ==========================================================
# LOGIN STEP 2 (OTP VERIFY)
# ==========================================================

@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    dependencies=[Depends(otp_verify_rate_limiter)]
)
def verify_otp(
    payload: OTPVerifyRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service)
):

    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")

    try:

        return service.verify_otp_and_login(
            payload.email,
            payload.otp,
            ip,
            user_agent
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "verify_otp_route_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="OTP verification failed"
        )


# ==========================================================
# RESEND OTP
# ==========================================================

@router.post(
    "/resend-otp",
    dependencies=[Depends(otp_resend_rate_limiter)]
)
def resend_otp(
    payload: ResendOTPRequest,
    service: AuthService = Depends(get_auth_service)
):

    try:
        return service.resend_otp(
            payload.email,
            payload.purpose
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ==========================================================
# FORGOT PASSWORD
# ==========================================================

@router.post(
    "/forgot-password",
    dependencies=[Depends(otp_resend_rate_limiter)]
)
def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service)
):

    try:

        return service.request_password_reset(payload.email)

    except Exception as e:

        log_event(
            "forgot_password_route_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to process request"
        )


# ==========================================================
# RESET PASSWORD
# ==========================================================

@router.post(
    "/reset-password",
    dependencies=[Depends(otp_verify_rate_limiter)]
)
def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service)
):

    try:

        return service.reset_password(
            payload.email,
            payload.otp,
            payload.new_password
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "reset_password_route_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Password reset failed"
        )


# ==========================================================
# REFRESH TOKEN
# ==========================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(api_rate_limiter)]
)
def refresh_token(
    payload: RefreshRequest,
    service: AuthService = Depends(get_auth_service)
):

    try:

        return service.refresh_access_token(
            payload.refresh_token
        )

    except ValueError as e:

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

    except Exception as e:

        log_event(
            "refresh_token_route_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Token refresh failed"
        )


# ==========================================================
# LOGOUT
# ==========================================================

@router.post("/logout")
def logout(
    payload: RefreshRequest,
    service: AuthService = Depends(get_auth_service)
):

    try:

        return service.logout(payload.refresh_token)

    except Exception as e:

        log_event(
            "logout_route_error",
            level="critical",
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Logout failed"
        )


# ==========================================================
# LOGOUT ALL DEVICES
# ==========================================================

@router.post("/logout-all")
def logout_all(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):

    service.session_service.delete_user_sessions(current_user["user_id"])

    return {"message": "All sessions revoked"}


# ==========================================================
# LOGIN HISTORY
# ==========================================================

@router.get("/login-history")
def login_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    service = LoginHistoryService(db)

    history = service.get_user_login_history(current_user["user_id"])

    return {
        "login_history": history
    }