"""
Admin Profile Model

Stores administrative metadata for platform administrators.

This model extends the base User model by adding admin-specific
attributes such as role, department, and access level.

Architecture:
User (authentication)
    ↓
AdminProfile (admin privileges)

Features:
- Role based access control
- Soft deletion
- Activity tracking
- Performance indexes
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Boolean,
    Enum,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum


# ==========================================================
# ADMIN ROLE ENUM
# ==========================================================

class AdminRole(str, enum.Enum):
    """
    Defines platform administrator roles.

    SUPER_ADMIN
        Full system control.

    ADMIN
        Standard platform administration.

    MODERATOR
        Limited moderation privileges.
    """

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"


# ==========================================================
# ADMIN PROFILE MODEL
# ==========================================================

class AdminProfile(Base):

    """
    AdminProfile

    Stores additional metadata for administrative users.

    Each admin profile is linked to a single User record.

    Fields:
    - role: admin permission level
    - department: admin organizational group
    - access_level: custom permission descriptor
    - is_active: whether admin access is enabled
    - last_login_at: admin login activity tracking
    """

    __tablename__ = "admin_profiles"

    # --------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------

    id = Column(Integer, primary_key=True, index=True)

    # --------------------------------------------------
    # USER RELATIONSHIP
    # --------------------------------------------------

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # --------------------------------------------------
    # ADMIN DETAILS
    # --------------------------------------------------

    department = Column(
        String(100),
        nullable=False
    )

    role = Column(
        Enum(AdminRole, name="admin_role_enum"),
        default=AdminRole.ADMIN,
        nullable=False,
        index=True
    )

    access_level = Column(
        String(50),
        nullable=True
    )

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    is_active = Column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False
    )

    # --------------------------------------------------
    # ACTIVITY TRACKING
    # --------------------------------------------------

    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # --------------------------------------------------
    # TIMESTAMPS
    # --------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Soft delete support
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # --------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------

    user = relationship(
        "User",
        back_populates="admin_profile"
    )

    # --------------------------------------------------
    # DATABASE INDEXES
    # --------------------------------------------------

    __table_args__ = (

        # Fast lookup by user
        Index("idx_admin_user", "user_id"),

        # Role filtering
        Index("idx_admin_role", "role"),

        # Role + active status filtering
        Index("idx_admin_role_active", "role", "is_active"),

        # Active admin lookup
        Index("idx_admin_active", "is_active"),
    )

    # --------------------------------------------------
    # DEBUG REPRESENTATION
    # --------------------------------------------------

    def __repr__(self):
        return f"<AdminProfile user_id={self.user_id} role={self.role}>"