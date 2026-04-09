"""
Customer Profile Model
======================

Stores customer-specific profile information.

Design Goals
------------
• Strict one-to-one relationship with User
• Supports future customer features
• Enterprise-grade audit timestamps
• Enum-based gender normalization
• Indexed fields for faster queries

Architecture
------------
User
   └── CustomerProfile
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    DateTime,
    Enum,
    Index
)

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base
import enum

# =========================================================
# GENDER ENUM
# =========================================================

class Gender(str, enum.Enum):
    """
    Standardized gender values.

    Using Enum ensures database consistency
    and prevents invalid values.
    """

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# =========================================================
# CUSTOMER PROFILE MODEL
# =========================================================

class CustomerProfile(Base):
    """
    CustomerProfile stores additional information for users
    who register as customers.

    This table extends the base User authentication table
    and contains customer-specific profile data.

    Relationship
    ------------
    User (1) ---- (1) CustomerProfile
    """

    __tablename__ = "customer_profiles"

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
    # PROFILE INFORMATION
    # --------------------------------------------------

    full_name = Column(
        String(255),
        nullable=False,
        index=True
    )

    gender = Column(
        Enum(Gender, name="gender_enum"),
        nullable=True
    )

    date_of_birth = Column(
        Date,
        nullable=True
    )

    # --------------------------------------------------
    # AUDIT TIMESTAMPS
    # --------------------------------------------------

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

    # --------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------

    user = relationship(
        "User",
        back_populates="customer_profile",
        passive_deletes=True
    )

    # --------------------------------------------------
    # DATABASE INDEXES
    # --------------------------------------------------

    __table_args__ = (
        Index("idx_customer_user", "user_id"),
    )