"""
Security Utilities

Handles:
- Password hashing
- JWT access token generation
- Refresh token generation
- Token hashing
- Token verification
- Secure comparison
"""

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import secrets
import hashlib
import uuid
import hmac

from app.core.config import settings
from app.core.logger import log_event


# ==========================================================
# JWT CONFIG
# ==========================================================

JWT_ISSUER = "luxora-auth"
JWT_AUDIENCE = "luxora-users"


# ==========================================================
# PASSWORD HASH CONTEXT
# ==========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


# ==========================================================
# PASSWORD HASHING
# ==========================================================

def hash_password(password: str) -> str:
    """
    Hash user password using bcrypt.
    """

    try:
        return pwd_context.hash(password)

    except Exception as e:

        log_event(
            "password_hash_error",
            level="critical",
            error=str(e)
        )

        raise ValueError("Unable to process password")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against stored hash.
    """

    try:
        return pwd_context.verify(plain_password, hashed_password)

    except Exception as e:

        log_event(
            "password_verify_error",
            level="critical",
            error=str(e)
        )

        return False


# ==========================================================
# ACCESS TOKEN CREATION
# ==========================================================

def create_access_token(
    data: Dict[str, Any],
    expires_minutes: int = None
) -> str:
    """
    Create signed JWT access token.
    """

    try:

        expires_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES

        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=expires_minutes)

        payload = data.copy()

        payload.update({
            "exp": expire,
            "iat": now,
            "nbf": now,
            "jti": str(uuid.uuid4()),
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "type": "access"
        })

        encoded_jwt = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        return encoded_jwt

    except Exception as e:

        log_event(
            "access_token_creation_error",
            level="critical",
            error=str(e)
        )

        raise ValueError("Unable to generate access token")


# ==========================================================
# REFRESH TOKEN GENERATION
# ==========================================================

def create_refresh_token() -> str:
    """
    Generate secure refresh token.
    """

    try:
        return secrets.token_urlsafe(64)

    except Exception as e:

        log_event(
            "refresh_token_generation_error",
            level="critical",
            error=str(e)
        )

        raise ValueError("Unable to generate refresh token")


# ==========================================================
# REFRESH TOKEN EXPIRY HELPER
# ==========================================================

def get_refresh_token_expiry():
    """
    Calculate refresh token expiry datetime.
    """

    return datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )


# ==========================================================
# HASH TOKEN
# ==========================================================

def hash_token(token: str) -> str:
    """
    Hash refresh token before storing in DB.
    """

    try:
        return hashlib.sha256(token.encode()).hexdigest()

    except Exception as e:

        log_event(
            "token_hash_error",
            level="critical",
            error=str(e)
        )

        raise ValueError("Unable to hash token")


# ==========================================================
# SECURE STRING COMPARISON
# ==========================================================

def secure_compare(val1: str, val2: str) -> bool:
    """
    Constant‑time comparison to prevent timing attacks.
    """

    try:
        return hmac.compare_digest(val1, val2)

    except Exception:

        return False


# ==========================================================
# VERIFY ACCESS TOKEN
# ==========================================================

def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Validate access token and return payload.
    """

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER
        )

        # Ensure correct token type
        if payload.get("type") != "access":
            raise JWTError("Invalid token type")

        # Ensure subject exists
        if "sub" not in payload:
            raise JWTError("Missing subject")

        return payload

    except JWTError:

        raise ValueError("Invalid or expired token")

    except Exception as e:

        log_event(
            "token_verification_error",
            level="critical",
            error=str(e)
        )

        raise ValueError("Token verification failed")