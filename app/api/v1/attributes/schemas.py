"""
Attribute Schemas

Pydantic models used for request validation and API responses.

Architecture:
Client → API Route → Schema Validation → Service Layer
"""

from pydantic import BaseModel, Field
from typing import List


# ==================================================
# CREATE ATTRIBUTE
# ==================================================

class AttributeCreate(BaseModel):
    """
    Request schema for creating a product attribute.

    Example:
        Color
        Size
        Storage
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Name of the attribute"
    )


# ==================================================
# CREATE ATTRIBUTE VALUE
# ==================================================

class AttributeValueCreate(BaseModel):
    """
    Request schema for creating an attribute value.

    Example:
        Attribute: Color
        Value: Red
    """

    value: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Value belonging to the attribute"
    )


# ==================================================
# ATTRIBUTE RESPONSE
# ==================================================

class AttributeResponse(BaseModel):
    """
    API response schema for attributes.
    """

    id: int
    name: str

    class Config:
        from_attributes = True


# ==================================================
# ATTRIBUTE VALUE RESPONSE
# ==================================================

class AttributeValueResponse(BaseModel):
    """
    API response schema for attribute values.
    """

    id: int
    attribute_id: int
    value: str

    class Config:
        from_attributes = True


# ==================================================
# ATTRIBUTE LIST RESPONSE
# ==================================================

class AttributeListResponse(BaseModel):
    """
    Response schema for listing attributes.
    """

    attributes: List[AttributeResponse]


# ==================================================
# ATTRIBUTE VALUE LIST RESPONSE
# ==================================================

class AttributeValueListResponse(BaseModel):
    """
    Response schema for listing attribute values.
    """

    values: List[AttributeValueResponse]


# ==================================================
# VARIANT ATTRIBUTE ASSIGN
# ==================================================

class VariantAttributeAssign(BaseModel):
    """
    Request schema for assigning attributes to a variant.

    Example:

        Variant: iPhone Black 128GB

        attribute_value_ids:
            [1, 5]
    """

    attribute_value_ids: List[int] = Field(
        ...,
        min_items=1,
        description="List of attribute value IDs to assign to the variant"
    )

# ==================================================
# ATTRIBUTE TREE RESPONSE
# ==================================================

class AttributeValueNestedResponse(BaseModel):
    """
    Nested attribute value response.
    """
    id: int
    value: str

    class Config:
        from_attributes = True


class AttributeTreeResponse(BaseModel):
    """
    Attribute tree response.

    Example:
    Color
    - Red
    - Blue
    """
    id: int
    name: str
    values: List[AttributeValueNestedResponse]

    class Config:
        from_attributes = True