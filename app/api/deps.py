"""
API Dependencies

Shared dependencies used across API routes.

Responsibilities:
- Provide database sessions
- Ensure safe session lifecycle
- Prevent connection leaks
- Handle rollback on failure

Architecture:
API Route → Dependency → Database Session
"""

from typing import Generator
from sqlalchemy.orm import Session

from app.infrastructure.database.session import SessionLocal
from app.core.logger import log_event


# ==================================================
# DATABASE SESSION DEPENDENCY
# ==================================================

def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for each request.

    Ensures:
    - Session creation
    - Automatic cleanup
    - Safe rollback on unexpected failures
    """

    db: Session = SessionLocal()

    try:
        yield db

    except Exception as e:

        # Rollback transaction if something failed
        db.rollback()

        log_event(
            "database_session_error",
            level="error",
            error=str(e)
        )

        raise

    finally:
        # Always close session
        db.close()