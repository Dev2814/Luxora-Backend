"""
Attack Detection Engine

Detects suspicious authentication activity.

Protects against:
• Credential stuffing
• OTP brute force
• Bot login attempts
• Suspicious IP behavior
"""

from typing import Optional

from app.infrastructure.redis.client import redis_client
from app.core.logger import log_event

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

MAX_LOGIN_FAILURES = 10
MAX_OTP_FAILURES = 10

FAILURE_WINDOW_SECONDS = 600
BLOCK_DURATION_SECONDS = 900


class AttackDetector:
    """
    Detects brute-force attacks using Redis counters.
    """

    # --------------------------------------------------
    # INTERNAL FAILURE TRACKER
    # --------------------------------------------------

    def _record_failure(
        self,
        key_prefix: str,
        ip: str,
        max_failures: int
    ) -> None:

        key = f"attack:{key_prefix}:{ip}"
        block_key = f"attack:block:{ip}"

        try:

            failures = redis_client.incr(key)

            # First failure → set expiration window
            if failures == 1:
                redis_client.expire(key, FAILURE_WINDOW_SECONDS)

            # Too many failures → block IP
            if failures >= max_failures:

                redis_client.setex(
                    block_key,
                    BLOCK_DURATION_SECONDS,
                    "1"
                )

                log_event(
                    "ip_blocked_security_attack",
                    level="critical",
                    ip=ip,
                    failures=failures,
                    attack_type=key_prefix
                )

        except Exception as e:

            log_event(
                "attack_detector_failure",
                level="critical",
                ip=ip,
                attack_type=key_prefix,
                error=str(e)
            )

    # --------------------------------------------------
    # LOGIN FAILURE
    # --------------------------------------------------

    def record_login_failure(self, ip: str) -> None:
        """
        Track failed login attempts.
        """
        self._record_failure("login_fail", ip, MAX_LOGIN_FAILURES)

    # --------------------------------------------------
    # OTP FAILURE
    # --------------------------------------------------

    def record_otp_failure(self, ip: str) -> None:
        """
        Track failed OTP attempts.
        """
        self._record_failure("otp_fail", ip, MAX_OTP_FAILURES)

    # --------------------------------------------------
    # RESET FAILURE COUNTERS
    # --------------------------------------------------

    def reset_failures(self, ip: str) -> None:
        """
        Reset failure counters after successful authentication.
        """

        try:

            redis_client.delete(
                f"attack:login_fail:{ip}",
                f"attack:otp_fail:{ip}"
            )

        except Exception as e:

            log_event(
                "attack_detector_reset_error",
                level="warning",
                ip=ip,
                error=str(e)
            )

    # --------------------------------------------------
    # CHECK IF IP IS BLOCKED
    # --------------------------------------------------

    def is_blocked(self, ip: str) -> bool:
        """
        Check if IP is currently blocked.
        """

        try:

            return redis_client.exists(f"attack:block:{ip}") == 1

        except Exception as e:

            log_event(
                "attack_detector_block_check_error",
                level="warning",
                ip=ip,
                error=str(e)
            )

            # Fail-safe → allow request
            return False


# --------------------------------------------------
# SINGLETON INSTANCE
# --------------------------------------------------

attack_detector = AttackDetector()