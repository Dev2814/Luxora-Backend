"""
Product Attribute System

Handles attributes and attribute values used for product variants.

Example:

Attribute: Color
Values: Red, Blue, Black

Attribute: Size
Values: S, M, L

Architecture:

Product
   └── Variant
          └── ProductAttributeMap
                 └── ProductAttributeValue
                        └── ProductAttribute

Design goals:
- Flexible variant attribute system
- Prevent duplicate attribute values
- Enable fast variant filtering
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
    DateTime,
    Index,
    Boolean
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


# =========================================================
# PRODUCT ATTRIBUTE
# =========================================================

class ProductAttribute(Base):
    """
    Represents an attribute type.

    Examples:
        Color
        Size
        Storage
        Material
    """

    __tablename__ = "product_attributes"

    id = Column(Integer, primary_key=True, index=True)

    # Attribute name
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )

    # Soft delete support
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationship to attribute values
    values = relationship(
        "ProductAttributeValue",
        back_populates="attribute",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# =========================================================
# PRODUCT ATTRIBUTE VALUE
# =========================================================

class ProductAttributeValue(Base):
    """
    Represents a value belonging to an attribute.

    Example:

        Attribute: Color
        Values:
            Red
            Blue
            Black
    """

    __tablename__ = "product_attribute_values"

    id = Column(Integer, primary_key=True, index=True)

    attribute_id = Column(
        Integer,
        ForeignKey("product_attributes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    value = Column(
        String(100),
        nullable=False,
        index=True
    )

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Parent attribute
    attribute = relationship(
        "ProductAttribute",
        back_populates="values"
    )

    # Mapping relationship to variants
    variant_maps = relationship(
        "ProductAttributeMap",
        back_populates="attribute_value",
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="attribute_values"
    )

    __table_args__ = (

        # Prevent duplicate values for same attribute
        UniqueConstraint(
            "attribute_id",
            "value",
            name="uq_attribute_value"
        ),

        # Performance index
        Index("idx_attribute_value_attribute", "attribute_id"),
    )


# =========================================================
# PRODUCT ATTRIBUTE MAP
# =========================================================

class ProductAttributeMap(Base):
    """
    Mapping table connecting variants to attribute values.

    Example:

        Variant:
            iPhone Black 128GB

        Attributes:
            Color -> Black
            Storage -> 128GB
    """

    __tablename__ = "product_attribute_map"

    id = Column(Integer, primary_key=True, index=True)

    variant_id = Column(
        Integer,
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    attribute_value_id = Column(
        Integer,
        ForeignKey("product_attribute_values.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Variant relationship
    variant = relationship(
        "ProductVariant",
        back_populates="attribute_maps",
        overlaps="attribute_values"
    )

    # Attribute value relationship
    attribute_value = relationship(
        "ProductAttributeValue",
        back_populates="variant_maps",
        overlaps="attribute_values"
    )

    __table_args__ = (

        # Prevent duplicate attribute assignments
        UniqueConstraint(
            "variant_id",
            "attribute_value_id",
            name="uq_variant_attribute_value"
        ),

        # Performance indexes
        Index("idx_variant_attribute_variant", "variant_id"),
        Index("idx_variant_attribute_value", "attribute_value_id"),
    )