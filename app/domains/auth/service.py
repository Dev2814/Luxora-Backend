"""
Auth Service

Handles authentication business logic.

Architecture:
Routes → Service → Repository → Database
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.domains.auth.repository import AuthRepository
from app.domains.auth.session_service import SessionService

from app.models.user import User, UserRole, AccountStatus
from app.models.customer_profile import CustomerProfile
from app.models.vendor_profile import VendorProfile, VendorStatus
from app.models.login_history import LoginHistory

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)

from app.core.attack_detector import attack_detector
from app.core.logger import log_event

from app.infrastructure.email.service import send_email

from app.domains.auth.otp_service import (
    generate_secure_otp,
    store_login_otp,
    verify_login_otp,
    store_reset_otp,
    verify_reset_otp
)

MAX_LOGIN_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15


class AuthService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)
        self.session_service = SessionService(db)

    # =====================================================
    # REGISTER USER
    # =====================================================

    def register_user(self, payload):

        try:
            existing_gst = self.repo.get_vendor_by_gst(payload.gst_number)
            email = payload.email.strip().lower()

            if payload.role not in ["customer", "vendor"]:
                raise ValueError("Invalid role")

            if self.repo.get_user_by_email(email):
                raise ValueError("Email already registered")

            if self.repo.get_user_by_phone(payload.phone):
                raise ValueError("Phone already registered")

            if existing_gst:
                raise ValueError("GST number already registered")   

            if len(payload.password) < 8:
                raise ValueError("Password must be at least 8 characters")

            user = User(
                email=email,
                phone=payload.phone,
                password_hash=hash_password(payload.password),
                role=UserRole(payload.role)
            )

            self.repo.create_user(user)

            self.db.flush()

            if payload.role == "customer":

                profile = CustomerProfile(
                    user_id=user.id,
                    full_name=payload.full_name,
                    gender=payload.gender,
                    date_of_birth=payload.date_of_birth
                )

                self.repo.create_customer_profile(profile)

            elif payload.role == "vendor":

                if not payload.business_name or not payload.business_address:
                    raise ValueError("Vendor business details required")

                store_name = payload.business_name
                store_slug = payload.business_name.lower().replace(" ", "-")

                profile = VendorProfile(
                    user_id=user.id,
                    store_name=store_name,
                    store_slug=store_slug,
                    business_name=payload.business_name,
                    business_address=payload.business_address,
                    gst_number=payload.gst_number,
                    verification_status=VendorStatus.PENDING
                )

                self.repo.create_vendor_profile(profile)

            self.db.commit()

            send_email(
                to_email=email,
                subject="Welcome to Luxora",
                template_name="welcome.html",
                context={
                    "email": email,
                    "title": "Welcome to Luxora",
                    "year": datetime.utcnow().year
                }
            )

            log_event("user_registered", user_id=user.id)

            return {"message": "Registration successful"}

        except SQLAlchemyError as e:

            self.db.rollback()

            log_event(
                "registration_database_error",
                level="critical",
                error=str(e)
            )

            raise ValueError("Registration failed")

    # =====================================================
    # LOGIN PASSWORD STEP
    # =====================================================

    def login_password_step(self, email: str, password: str, ip: str, user_agent: str):

        email = email.strip().lower()

        if attack_detector.is_blocked(ip):
            raise ValueError("Too many failed attempts. Try again later.")

        user = self.repo.get_user_by_email(email)

        if not user:

            attack_detector.record_login_failure(ip)

            self.repo.create_login_history(
                LoginHistory(
                    email=email,
                    success=False,
                    failure_reason="user_not_found",
                    ip_address=ip,
                    user_agent=user_agent
                )
            )

            raise ValueError("Invalid credentials")

        if user.status != AccountStatus.ACTIVE:
            raise ValueError("Account inactive")

        if user.lock_until and user.lock_until > datetime.utcnow():
            raise ValueError("Account temporarily locked")

        if not verify_password(password, user.password_hash):

            attack_detector.record_login_failure(ip)

            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:

                user.lock_until = datetime.utcnow() + timedelta(
                    minutes=LOCK_DURATION_MINUTES
                )

                log_event("account_locked", user_id=user.id)

            self.db.commit()

            self.repo.create_login_history(
                LoginHistory(
                    user_id=user.id,
                    email=email,
                    success=False,
                    failure_reason="invalid_password",
                    ip_address=ip,
                    user_agent=user_agent
                )
            )

            raise ValueError("Invalid credentials")

        user.failed_login_attempts = 0
        user.lock_until = None
        self.db.commit()

        otp = generate_secure_otp()

        print(f"Generated OTP for login: {otp}")  # Debug log

        store_login_otp(user.id, otp)

        send_email(
            to_email=email,
            subject="Luxora Login Verification Code",
            template_name="login_otp.html",
            context={
                "otp": otp,
                "title": "Luxora Login Verification",
                "year": datetime.utcnow().year
            }
        )

        log_event("login_otp_sent", user_id=user.id)

        return {"message": "OTP sent to email"}

    # =====================================================
    # VERIFY OTP AND LOGIN
    # =====================================================

    def verify_otp_and_login(self, email: str, otp: str, ip: str, user_agent: str):

        email = email.strip().lower()

        user = self.repo.get_user_by_email(email)

        if not user:
            raise ValueError("Invalid request")

        if not verify_login_otp(user.id, otp):

            attack_detector.record_otp_failure(ip)

            raise ValueError("Invalid OTP")

        if user.role == UserRole.VENDOR:

            vendor = self.repo.get_vendor_profile(user.id)

            if not vendor or vendor.verification_status != VendorStatus.APPROVED:
                raise ValueError("Vendor not approved")

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role.value}
        )

        refresh_token = self.session_service.create_session(
            user.id,
            ip,
            user_agent
        )

        self.repo.create_login_history(
            LoginHistory(
                user_id=user.id,
                email=email,
                success=True,
                ip_address=ip,
                user_agent=user_agent
            )
        )

        log_event(
            "user_logged_in",
            user_id=user.id,
            ip=ip
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    # =====================================================
    # RESEND OTP
    # =====================================================

    def resend_otp(self, email: str, purpose: str):

        email = email.strip().lower()

        user = self.repo.get_user_by_email(email)

        if not user:
            raise ValueError("User not found")

        otp = generate_secure_otp()

        print(f"Generated RESEND OTP for {purpose}: {otp}")  # Debug log

        if purpose == "login":

            store_login_otp(user.id, otp)

            template = "login_otp.html"
            subject = "Luxora Login Verification Code"

        elif purpose == "reset":

            store_reset_otp(user.id, otp)

            template = "forgot_password.html"
            subject = "Password Reset OTP"

        else:
            raise ValueError("Invalid OTP purpose")

        send_email(
            to_email=email,
            subject=subject,
            template_name=template,
            context={
                "otp": otp,
                "title": "Luxora Verification",
                "year": datetime.utcnow().year
            }
        )

        log_event(
            "otp_resent",
            user_id=user.id,
            purpose=purpose
        )

        return {"message": "OTP resent successfully"}

    # =====================================================
    # PASSWORD RESET REQUEST
    # =====================================================

    def request_password_reset(self, email: str):

        email = email.strip().lower()

        user = self.repo.get_user_by_email(email)

        if not user:
            return {"message": "If the email exists, reset instructions were sent."}

        otp = generate_secure_otp()

        print(f"Generated OTP for password reset: {otp}")  # Debug log

        store_reset_otp(user.id, otp)

        send_email(
            to_email=email,
            subject="Password Reset OTP",
            template_name="forgot_password.html",
            context={
                "otp": otp,
                "title": "Luxora Password Reset",
                "year": datetime.utcnow().year
            }
        )

        log_event("password_reset_requested", user_id=user.id)

        return {"message": "OTP sent"}

    # =====================================================
    # RESET PASSWORD
    # =====================================================

    def reset_password(self, email: str, otp: str, new_password: str):

        email = email.strip().lower()

        user = self.repo.get_user_by_email(email)

        if not user:
            raise ValueError("Invalid request")

        if not verify_reset_otp(user.id, otp):
            raise ValueError("Invalid OTP")

        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        user.failed_login_attempts = 0
        user.lock_until = None

        self.repo.delete_user_sessions(user.id)

        self.db.commit()

        send_email(
            to_email=email,
            subject="Your Luxora Password Was Changed",
            template_name="password_changed.html",
            context={
                "title": "Password Updated",
                "year": datetime.utcnow().year
            }
        )

        log_event("password_changed", user_id=user.id)

        return {"message": "Password updated"}

    # =====================================================
    # REFRESH TOKEN
    # =====================================================

    def refresh_access_token(self, refresh_token: str):

        session = self.session_service.get_session(refresh_token)

        if not session:
            raise ValueError("Invalid refresh token")

        if session.expires_at < datetime.utcnow():
            raise ValueError("Refresh token expired")

        user = self.repo.get_user_by_id(session.user_id)

        if user.status != AccountStatus.ACTIVE:
            raise ValueError("Account inactive")

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role.value}
        )

        new_refresh_token = self.session_service.rotate_refresh_token(session)

        log_event("access_token_refreshed", user_id=user.id)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    # =====================================================
    # LOGOUT
    # =====================================================

    def logout(self, refresh_token: str):

        self.session_service.delete_session(refresh_token)

        return {"message": "Logged out"}