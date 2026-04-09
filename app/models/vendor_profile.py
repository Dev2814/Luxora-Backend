"""
Vendor Profile Model

Stores marketplace vendor information and verification status.

This model represents a seller account in the Luxora platform.

Architecture:

User
   ↓
VendorProfile
   ↓
Products
   ↓
Orders

Key Features:
- Vendor verification workflow
- Store identity (name, slug, branding)
- Commission configuration
- Vendor status management
- Audit timestamps
- Optimized database indexes
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    Enum,
    Numeric,
    Boolean,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum


# ======================================================
# VENDOR VERIFICATION STATUS ENUM
# ======================================================

class VendorStatus(str, enum.Enum):
    """
    Vendor verification lifecycle.

    pending   → vendor applied but not reviewed
    approved  → vendor allowed to sell
    rejected  → vendor rejected by admin
    suspended → vendor temporarily blocked
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


# ======================================================
# VENDOR PROFILE MODEL
# ======================================================

class VendorProfile(Base):
    """
    Represents a seller account on the platform.

    Each vendor profile belongs to exactly one User.

    Example:

    User
       id = 12

    VendorProfile
       store_name = "Apple Official"
       verification_status = APPROVED
       commission_rate = 5%
    """

    __tablename__ = "vendor_profiles"

    # ======================================================
    # PRIMARY KEY
    # ======================================================

    id = Column(Integer, primary_key=True, index=True)

    # ======================================================
    # USER RELATIONSHIP
    # ======================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # ======================================================
    # STORE INFORMATION
    # ======================================================

    store_name = Column(
        String(255),
        nullable=False,
        index=True
    )

    store_slug = Column(
        String(255),
        unique=True,
        index=True
    )

    store_logo = Column(
        String(500),
        nullable=True
    )

    store_description = Column(
        Text,
        nullable=True
    )

    # ======================================================
    # BUSINESS INFORMATION
    # ======================================================

    business_name = Column(
        String(255),
        nullable=False
    )

    gst_number = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True
    )

    business_address = Column(
        String(500),
        nullable=False
    )

    # ======================================================
    # VENDOR VERIFICATION SYSTEM
    # ======================================================

    verification_status = Column(
        Enum(VendorStatus),
        default=VendorStatus.PENDING,
        nullable=False,
        index=True
    )

    verified_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    rejection_reason = Column(
        Text,
        nullable=True
    )

    # ======================================================
    # PLATFORM SETTINGS
    # ======================================================

    commission_rate = Column(
        Numeric(5, 2),
        default=5.00,
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # ======================================================
    # AUDIT TIMESTAMPS
    # ======================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ======================================================
    # RELATIONSHIPS
    # ======================================================

    # Link to the main user account
    user = relationship(
        "User",
        back_populates="vendor_profile",
        passive_deletes=True
    )

    # All products owned by this vendor
    products = relationship(
        "Product",
        back_populates="vendor",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # ======================================================
    # DATABASE INDEXES
    # ======================================================

    __table_args__ = (

        # Fast vendor lookup by user
        Index("idx_vendor_user", "user_id"),

        # Vendor verification filtering
        Index("idx_vendor_status", "verification_status"),

        # GST search
        Index("idx_vendor_gst", "gst_number"),
    )