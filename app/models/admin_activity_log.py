"""
Admin Activity Log Model

Stores all administrative actions for auditing.

Used for:
- security investigations
- compliance logging
- admin accountability
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class AdminActivityLog(Base):

    __tablename__ = "admin_activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    # --------------------------------------------------
    # ADMIN USER REFERENCE
    # --------------------------------------------------

    admin_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # --------------------------------------------------
    # ACTION INFO
    # --------------------------------------------------

    action = Column(
        String(100),
        nullable=False,
        index=True
    )

    target_type = Column(String(100), nullable=True)

    target_id = Column(Integer, nullable=True)

    # additional structured information
    extra_data = Column(JSON, nullable=True)

    # --------------------------------------------------
    # REQUEST CONTEXT
    # --------------------------------------------------

    ip_address = Column(String(100), nullable=True)

    user_agent = Column(String(500), nullable=True)

    severity = Column(
        String(20),
        default="INFO"
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

    admin = relationship(
        "User",
        back_populates="admin_activity_logs",
        foreign_keys=[admin_id]
    )

    # --------------------------------------------------
    # INDEXES
    # --------------------------------------------------

    __table_args__ = (
        Index("idx_admin_action", "action"),
        Index("idx_admin_target", "target_type", "target_id"),
        Index("idx_admin_admin_time", "admin_id", "created_at"),
    )