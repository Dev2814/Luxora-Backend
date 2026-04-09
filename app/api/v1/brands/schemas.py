"""
Brand Schemas
=============

Defines API contracts for Brand.
"""

from pydantic import BaseModel
from typing import Optional


# ======================================================
# CREATE REQUEST (ADMIN)
# ======================================================

class BrandCreateRequest(BaseModel):
    name: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


# ======================================================
# RESPONSE
# ======================================================

class BrandResponse(BaseModel):
    id: int
    name: str
    logo: Optional[str]
    slug: str
    meta_title: Optional[str]
    meta_description: Optional[str]

    class Config:
        from_attributes = True