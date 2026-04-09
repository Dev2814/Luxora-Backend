"""
Login History Model

Tracks all login attempts for security monitoring.

Features:
- successful login tracking
- failed login tracking
- IP tracking
- device tracking
- suspicious activity detection
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class LoginHistory(Base):

    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)

    # --------------------------------------------------
    # USER RELATION
    # --------------------------------------------------

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    email = Column(
        String(255),
        nullable=True,
        index=True
    )

    # --------------------------------------------------
    # LOGIN RESULT
    # --------------------------------------------------

    success = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    failure_reason = Column(
        String(255),
        nullable=True
    )

    # --------------------------------------------------
    # DEVICE / NETWORK INFO
    # --------------------------------------------------

    ip_address = Column(
        String(100),
        nullable=True,
        index=True
    )

    user_agent = Column(
        String(500),
        nullable=True
    )

    device_name = Column(
        String(255),
        nullable=True
    )

    country = Column(
        String(100),
        nullable=True
    )

    city = Column(
        String(100),
        nullable=True
    )

    # --------------------------------------------------
    # SECURITY FLAGS
    # --------------------------------------------------

    is_suspicious = Column(
        Boolean,
        default=False,
        index=True
    )

    # --------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    # --------------------------------------------------
    # RELATIONSHIP
    # --------------------------------------------------

    user = relationship(
        "User",
        backref="login_history",
        passive_deletes=True
    )

    # --------------------------------------------------
    # INDEXES
    # --------------------------------------------------

    __table_args__ = (
        Index("idx_login_user_time", "user_id", "created_at"),
        Index("idx_login_ip", "ip_address"),
    )