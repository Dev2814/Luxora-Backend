"""
Category Schemas

Pydantic models used for category API validation and responses.

Responsibilities:
- Validate incoming API payloads
- Standardize API responses
- Prevent invalid category data
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# ==================================================
# CREATE CATEGORY
# ==================================================

class CategoryCreate(BaseModel):
    """
    Request schema for creating a new category.
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Category display name"
    )

    slug: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="URL friendly category slug"
    )

    parent_id: Optional[int] = Field(
        None,
        description="Parent category ID (for nested categories)"
    )

    description: Optional[str] = Field(
        None,
        max_length=1000
    )

    meta_title: Optional[str] = Field(
        None,
        max_length=255
    )

    meta_description: Optional[str] = Field(
        None,
        max_length=500
    )

# ==================================================
# UPDATE CATEGORY
# ==================================================

class CategoryUpdate(BaseModel):
    """
    Request schema for updating a category.
    """

    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255
    )

    slug: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255
    )

    parent_id: Optional[int]

    description: Optional[str]

    meta_title: Optional[str]

    meta_description: Optional[str]

    is_active: Optional[bool]

# ==================================================
# CATEGORY RESPONSE
# ==================================================

class CategoryResponse(BaseModel):
    """
    Standard category API response.
    """

    id: int
    name: str
    slug: str
    parent_id: Optional[int]

    description: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

    children_count: int = 0

    class Config:
        from_attributes = True

# ==================================================
# CATEGORY TREE RESPONSE
# ==================================================

class CategoryTreeResponse(BaseModel):
    """
    Recursive category tree structure.
    """

    id: int
    name: str
    slug: str
    parent_id: Optional[int]

    # 🔥 NEW (SEO SUPPORT)
    description: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

    children: List["CategoryTreeResponse"] = []

    class Config:
        from_attributes = True


# Fix recursive model reference
CategoryTreeResponse.model_rebuild()