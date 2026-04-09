"""
User Model

Central identity model for the platform.

All system actors inherit from this user:
- Customers
- Vendors
- Admins

Responsibilities:
- Authentication credentials
- Account status management
- Security tracking (login attempts, lockouts)
- Relationship to profile systems
- Relationship to sessions and admin logs

Architecture:

User
 ├── CustomerProfile
 ├── VendorProfile
 ├── AdminProfile
 ├── UserSession
 └── AdminActivityLog
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Enum,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base
import enum


# ==================================================
# USER ROLE ENUM
# ==================================================

class UserRole(str, enum.Enum):
    """
    Defines the type of user account.

    CUSTOMER → platform buyers
    VENDOR   → marketplace sellers
    ADMIN    → platform administrators
    """

    CUSTOMER = "customer"
    VENDOR = "vendor"
    ADMIN = "admin"


# ==================================================
# ACCOUNT STATUS ENUM
# ==================================================

class AccountStatus(str, enum.Enum):
    """
    Controls whether the user account is usable.

    ACTIVE   → normal account
    LOCKED   → temporarily locked due to security
    DISABLED → manually disabled by admin
    DELETED  → soft deleted account
    """

    ACTIVE = "active"
    LOCKED = "locked"
    DISABLED = "disabled"
    DELETED = "deleted"


# ==================================================
# USER MODEL
# ==================================================

class User(Base):
    """
    Core authentication and identity model.

    All users authenticate through this table.
    Profiles extend the user into role-specific data.
    """

    __tablename__ = "users"

    # --------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------

    id = Column(Integer, primary_key=True, index=True)

    # --------------------------------------------------
    # AUTHENTICATION FIELDS
    # --------------------------------------------------

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    phone = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        Enum(UserRole),
        nullable=False,
        index=True
    )

    # --------------------------------------------------
    # ACCOUNT STATUS
    # --------------------------------------------------

    status = Column(
        Enum(AccountStatus),
        default=AccountStatus.ACTIVE,
        nullable=False,
        index=True
    )

    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    # --------------------------------------------------
    # SECURITY PROTECTION
    # --------------------------------------------------

    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False
    )

    lock_until = Column(
        DateTime(timezone=True),
        nullable=True
    )

    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    last_login_ip = Column(
        String(100),
        nullable=True
    )

    password_changed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    email_verified_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # --------------------------------------------------
    # AUDIT TIMESTAMPS
    # --------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # ==================================================
    # RELATIONSHIPS
    # ==================================================

    # --------------------------------------------------
    # CUSTOMER PROFILE (1:1)
    # --------------------------------------------------

    customer_profile = relationship(
        "CustomerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # --------------------------------------------------
    # WISHLIST (1:1)
    # --------------------------------------------------

    wishlist = relationship(
        "Wishlist",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # --------------------------------------------------
    # REVIEWS (1:N)
    # --------------------------------------------------

    reviews = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # --------------------------------------------------
    # CUSTOMER CART 
    # --------------------------------------------------

    cart = relationship(
        "Cart",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # --------------------------------------------------
    # CUSTOMER ORDERS 
    # --------------------------------------------------

    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # --------------------------------------------------
    # COUPON USAGES
    # --------------------------------------------------

    coupon_usages = relationship(
        "CouponUsage",
        back_populates="user"
    )

    # --------------------------------------------------
    # ADMIN ACTIVITY LOGS
    # --------------------------------------------------

    admin_activity_logs = relationship(
        "AdminActivityLog",
        back_populates="admin",
        foreign_keys="[AdminActivityLog.admin_id]",
        passive_deletes=True
    )

    # --------------------------------------------------
    # VENDOR PROFILE (1:1)
    # --------------------------------------------------

    vendor_profile = relationship(
        "VendorProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # --------------------------------------------------
    # ADMIN PROFILE (1:1)
    # --------------------------------------------------

    admin_profile = relationship(
        "AdminProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # --------------------------------------------------
    # USER SESSIONS (1:N)
    # --------------------------------------------------

    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # --------------------------------------------------
    # USER ADDRESSES (1:N)
    # --------------------------------------------------

    addresses = relationship(
        "UserAddress",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


    # ==================================================
    # DATABASE INDEXES
    # ==================================================

    __table_args__ = (

        # Fast authentication lookup
        Index("idx_user_email", "email"),

        # Phone based login lookup
        Index("idx_user_phone", "phone"),

        # Role filtering
        Index("idx_user_role", "role"),

        # Account status filtering
        Index("idx_user_status", "status"),
    )