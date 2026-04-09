import uuid

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class UserSession(Base):

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)

    session_uuid = Column(
        String(36),
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    refresh_token_hash = Column(
        String(255),
        nullable=False,
        index=True
    )

    ip_address = Column(String(100), nullable=True)

    user_agent = Column(String(500), nullable=True)

    device_name = Column(String(255), nullable=True)

    device_fingerprint = Column(String(255), nullable=True)

    country = Column(String(100), nullable=True)

    is_revoked = Column(Boolean, default=False, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    last_used_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship(
        "User",
        back_populates="sessions"
    )

    __table_args__ = (
        Index("idx_user_session_user", "user_id"),
        Index("idx_user_session_token", "refresh_token_hash"),
        Index("idx_user_session_expiry", "expires_at"),
    )