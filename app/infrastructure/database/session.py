"""
Database Session Management

Provides:
- SQLAlchemy engine configuration
- Connection pooling
- Session factory
- FastAPI dependency

Enterprise features:
- connection pool tuning
- stale connection protection
- safe session lifecycle
- structured error logging
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logger import log_event


# ======================================================
# DATABASE ENGINE
# ======================================================

try:

    engine = create_engine(
        str(settings.DATABASE_URL),  # convert AnyUrl → string

        # -----------------------------
        # CONNECTION POOL
        # -----------------------------
        pool_size=10,          # number of permanent connections
        max_overflow=20,       # temporary overflow connections
        pool_timeout=30,       # seconds to wait for connection
        pool_recycle=1800,     # recycle connection (30 min)

        # -----------------------------
        # CONNECTION SAFETY
        # -----------------------------
        pool_pre_ping=True,    # detect stale MySQL connections
        pool_reset_on_return="rollback",

        # -----------------------------
        # SQLAlchemy 2.0 mode
        # -----------------------------
        future=True,

        # -----------------------------
        # Debug logging (disable in prod)
        # -----------------------------
        echo=False
    )

    log_event("database_engine_initialized")

except Exception as e:

    log_event(
        "database_engine_init_failed",
        level="critical",
        error=str(e)
    )

    raise


# ======================================================
# SESSION FACTORY
# ======================================================

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


# ======================================================
# FASTAPI DATABASE DEPENDENCY
# ======================================================

def get_db():
    """
    FastAPI dependency for database sessions.
    Ensures safe transaction handling.
    """

    db = SessionLocal()

    try:

        yield db

    except SQLAlchemyError as e:

        log_event(
            event="database_session_error",
            level="critical",
            error=str(e)
        )

        db.rollback()
        raise

    finally:

        db.close()