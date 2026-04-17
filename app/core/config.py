"""
Application Configuration

Loads environment variables using Pydantic Settings.

Supports:
- Database configuration
- Redis configuration
- JWT authentication
- Email service
- Environment control
- Security validation
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyUrl
from typing import Optional


class Settings(BaseSettings):

    # --------------------------------------------------
    # APPLICATION
    # --------------------------------------------------

    APP_NAME: str = "Luxora Backend"
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment name (development, staging, production)"
    )

    DEBUG: bool = False

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------

    DATABASE_URL: AnyUrl = Field(
        ...,
        description="Primary database connection URL"
    )

    # --------------------------------------------------
    # REDIS
    # --------------------------------------------------

    REDIS_URL: AnyUrl = Field(
        ...,
        description="Redis connection URL"
    )

    # --------------------------------------------------
    # JWT SECURITY
    # --------------------------------------------------

    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="JWT secret key"
    )

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1
    )

    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1
    )

    # --------------------------------------------------
    # EMAIL SERVICE
    # --------------------------------------------------

    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None

    MAIL_PORT: int = 587
    MAIL_SERVER: Optional[str] = None

    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # --------------------------------------------------
    # STRIPE PAYMENT CONFIGURATION
    # --------------------------------------------------

    STRIPE_PUBLIC_KEY: str = Field(
        ...,
        description="Stripe publishable key (pk_test / pk_live)"
    )

    STRIPE_SECRET_KEY: str = Field(
        ...,
        description="Stripe secret API key (sk_test / sk_live)"
    )

    STRIPE_WEBHOOK_SECRET: str = Field(
        ...,
        description="Stripe webhook signing secret (whsec)"
    )

    # --------------------------------------------------
    # ADMIN ALERT EMAIL
    # --------------------------------------------------

    ADMIN_ALERT_EMAIL: Optional[str] = None

    # --------------------------------------------------
    # SECURITY / RATE LIMITING
    # --------------------------------------------------

    LOGIN_RATE_LIMIT: int = 5
    API_RATE_LIMIT: int = 100

    # --------------------------------------------------
    # Firebase Configuration
    # --------------------------------------------------

    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(
        default=None,
        description="Path to Firebase service account JSON file")

    # --------------------------------------------------
    # SETTINGS CONFIG
    # --------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# --------------------------------------------------
# GLOBAL SETTINGS INSTANCE
# --------------------------------------------------

settings = Settings()