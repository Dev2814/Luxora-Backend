"""
OTP Service

Handles login OTP and password reset OTP.

Enterprise security features:
- OTP hashing
- attempt limit protection
- replay protection
- Redis TTL expiration
- OTP request throttling
"""

import secrets
import hashlib
from typing import Optional

from app.infrastructure.redis.client import redis_client
from app.core.logger import log_event

OTP_LENGTH = 6
OTP_TTL_SECONDS = 300
RESET_OTP_TTL_SECONDS = 300
MAX_OTP_ATTEMPTS = 5
OTP_REQUEST_LIMIT = 3


# ==========================================================
# KEY BUILDERS
# ==========================================================

def _otp_key(prefix: str, user_id: int) -> str:
    return f"otp:{prefix}:{user_id}"


def _otp_request_key(prefix: str, user_id: int) -> str:
    return f"otp_request:{prefix}:{user_id}"


# ==========================================================
# OTP GENERATION
# ==========================================================

def generate_secure_otp(length: int = OTP_LENGTH) -> str:
    """
    Generate cryptographically secure OTP.
    """
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


# ==========================================================
# HASH OTP
# ==========================================================

def hash_otp(otp: str) -> str:
    """
    Hash OTP using SHA256 before storing.
    """
    return hashlib.sha256(otp.encode()).hexdigest()


# ==========================================================
# REQUEST THROTTLING
# ==========================================================

def _check_request_limit(prefix: str, user_id: int) -> bool:

    key = _otp_request_key(prefix, user_id)

    try:

        count = redis_client.incr(key)

        if count == 1:
            redis_client.expire(key, OTP_TTL_SECONDS)

        if count > OTP_REQUEST_LIMIT:

            log_event(
                "otp_request_limit_reached",
                level="warning",
                user_id=user_id,
                prefix=prefix
            )

            return False

        return True

    except Exception as e:

        log_event(
            "otp_request_limit_error",
            level="critical",
            user_id=user_id,
            error=str(e)
        )

        # Fail‑safe: allow request if Redis fails
        return True


# ==========================================================
# STORE OTP
# ==========================================================

def _store_otp(prefix: str, otp: str, ttl: int, user_id: int):

    key = _otp_key(prefix, user_id)

    if not _check_request_limit(prefix, user_id):
        raise ValueError("Too many OTP requests")

    try:

        otp_hash = hash_otp(otp)

        pipe = redis_client.pipeline()

        pipe.hset(
            key,
            mapping={
                "otp_hash": otp_hash,
                "attempts": 0
            }
        )

        pipe.expire(key, ttl)

        pipe.execute()

        log_event(
            "otp_stored",
            user_id=user_id,
            prefix=prefix
        )

    except Exception as e:

        log_event(
            "otp_store_error",
            level="critical",
            user_id=user_id,
            error=str(e)
        )

        raise ValueError("Unable to store OTP")


# ==========================================================
# VERIFY OTP
# ==========================================================

def _verify_otp(prefix: str, otp: str, user_id: int) -> bool:

    key = _otp_key(prefix, user_id)

    try:

        data = redis_client.hgetall(key)

        if not data:

            log_event(
                "otp_not_found",
                level="warning",
                user_id=user_id,
                prefix=prefix
            )

            return False

        # Redis may return bytes
        stored_hash = data.get("otp_hash")
        attempts = data.get("attempts", 0)

        if isinstance(stored_hash, bytes):
            stored_hash = stored_hash.decode()

        if isinstance(attempts, bytes):
            attempts = attempts.decode()

        attempts = int(attempts)

        # --------------------------------------------------
        # ATTEMPT LIMIT
        # --------------------------------------------------

        if attempts >= MAX_OTP_ATTEMPTS:

            redis_client.delete(key)

            log_event(
                "otp_attempt_limit_reached",
                level="warning",
                user_id=user_id,
                prefix=prefix
            )

            return False

        incoming_hash = hash_otp(otp)

        # --------------------------------------------------
        # VERIFY OTP
        # --------------------------------------------------

        if stored_hash and secrets.compare_digest(incoming_hash, stored_hash):

            # delete to prevent replay attack
            redis_client.delete(key)

            log_event(
                "otp_verified",
                user_id=user_id,
                prefix=prefix
            )

            return True

        # --------------------------------------------------
        # WRONG OTP
        # --------------------------------------------------

        redis_client.hincrby(key, "attempts", 1)

        log_event(
            "otp_failed",
            level="warning",
            user_id=user_id,
            prefix=prefix,
            attempts=attempts + 1
        )

        return False

    except Exception as e:

        log_event(
            "otp_verify_error",
            level="critical",
            user_id=user_id,
            error=str(e)
        )

        return False


# ==========================================================
# LOGIN OTP
# ==========================================================

def store_login_otp(user_id: int, otp: str):

    _store_otp("login", otp, OTP_TTL_SECONDS, user_id)


def verify_login_otp(user_id: int, otp: str) -> bool:

    return _verify_otp("login", otp, user_id)


# ==========================================================
# PASSWORD RESET OTP
# ==========================================================

def store_reset_otp(user_id: int, otp: str):

    _store_otp("reset", otp, RESET_OTP_TTL_SECONDS, user_id)


def verify_reset_otp(user_id: int, otp: str) -> bool:

    return _verify_otp("reset", otp, user_id)