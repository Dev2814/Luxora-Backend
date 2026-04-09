"""
Auth Schemas

Defines request and response models for authentication APIs.
Ensures strict validation and secure API contracts.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from datetime import date
from typing import Optional
from enum import Enum
import re


# ==========================================================
# ENUMS
# ==========================================================

class UserRole(str, Enum):
    customer = "customer"
    vendor = "vendor"


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


# ==========================================================
# BASE SCHEMA CONFIG
# ==========================================================

class BaseSchema(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True
    )


# ==========================================================
# PASSWORD VALIDATION
# ==========================================================

def validate_password_strength(password: str) -> str:

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    if len(password) > 128:
        raise ValueError("Password too long")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain an uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain a lowercase letter")

    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain a number")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain a special character")

    return password


# ==========================================================
# REGISTER REQUEST
# ==========================================================

class RegisterRequest(BaseSchema):

    role: UserRole

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    email: EmailStr

    phone: str

    password: str

    gender: Gender

    date_of_birth: date

    # Vendor fields
    business_name: Optional[str] = Field(None, max_length=200)
    business_address: Optional[str] = Field(None, max_length=500)
    gst_number: Optional[str] = Field(None, max_length=20)

    # ------------------------------------------------------
    # VALIDATORS
    # ------------------------------------------------------

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str):

        value = re.sub(r"\s+", "", value)

        if not re.fullmatch(r"\+?[1-9]\d{9,14}", value):
            raise ValueError("Invalid phone number format")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        return validate_password_strength(value)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        return value.lower().strip()

    # ------------------------------------------------------
    # ROLE BASED VALIDATION
    # ------------------------------------------------------

    @model_validator(mode="after")
    def validate_role_fields(self):

        if self.role == UserRole.vendor:

            if not self.business_name:
                raise ValueError("Vendor business_name required")

            if not self.business_address:
                raise ValueError("Vendor business_address required")

        return self


# ==========================================================
# LOGIN REQUEST
# ==========================================================

class LoginRequest(BaseSchema):

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        return value.lower().strip()


# ==========================================================
# OTP VERIFY REQUEST
# ==========================================================

class OTPVerifyRequest(BaseSchema):

    email: EmailStr

    otp: str = Field(
        ...,
        min_length=6,
        max_length=6
    )

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str):

        if not value.isdigit():
            raise ValueError("OTP must be numeric")

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        return value.lower().strip()


# ==========================================================
# RESEND OTP REQUEST
# ==========================================================

class ResendOTPRequest(BaseSchema):

    email: EmailStr
    purpose: str

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str):

        allowed = {"login", "reset"}

        if value not in allowed:
            raise ValueError("Purpose must be 'login' or 'reset'")

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        return value.lower().strip()


# ==========================================================
# FORGOT PASSWORD REQUEST
# ==========================================================

class ForgotPasswordRequest(BaseSchema):

    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        return value.lower().strip()


# ==========================================================
# RESET PASSWORD REQUEST
# ==========================================================

class ResetPasswordRequest(BaseSchema):

    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str):

        if not value.isdigit():
            raise ValueError("OTP must be numeric")

        return value

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str):
        return validate_password_strength(value)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str):
        return value.lower().strip()


# ==========================================================
# REFRESH TOKEN REQUEST
# ==========================================================

class RefreshRequest(BaseSchema):

    refresh_token: str = Field(
        ...,
        min_length=20,
        max_length=500
    )


# ==========================================================
# TOKEN RESPONSE
# ==========================================================

class TokenResponse(BaseSchema):

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"