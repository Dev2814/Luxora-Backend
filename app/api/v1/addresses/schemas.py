"""
Address Schemas
===============

Pydantic schemas used for request validation and response
serialization for user address management.

Responsibilities
----------------
• Address creation validation
• Address update validation
• API response formatting

Architecture
------------
Client → API Schema → Service → Repository → Database
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


# =========================================================
# ADDRESS CREATE
# =========================================================

class AddressCreate(BaseModel):
    """
    Schema used when creating a new user address.
    """

    label: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Address label (Home, Office, etc.)"
    )

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Recipient full name"
    )

    phone_number: str = Field(
        ...,
        min_length=8,
        max_length=20,
        description="Contact phone number"
    )

    address_line1: str = Field(
        ...,
        max_length=255
    )

    address_line2: Optional[str] = Field(
        default=None,
        max_length=255
    )

    city: str = Field(
        ...,
        max_length=100
    )

    state: str = Field(
        ...,
        max_length=100
    )

    postal_code: str = Field(
        ...,
        max_length=20
    )

    country: Optional[str] = Field(
        default="India",
        max_length=100
    )

    is_default: bool = Field(
        default=False
    )


# =========================================================
# ADDRESS UPDATE
# =========================================================

class AddressUpdate(BaseModel):
    """
    Schema used for updating an existing address.
    """

    label: Optional[str] = Field(default=None, max_length=50)

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)

    phone_number: Optional[str] = Field(default=None, min_length=8, max_length=20)

    address_line1: Optional[str] = Field(default=None, max_length=255)

    address_line2: Optional[str] = Field(default=None, max_length=255)

    city: Optional[str] = Field(default=None, max_length=100)

    state: Optional[str] = Field(default=None, max_length=100)

    postal_code: Optional[str] = Field(default=None, max_length=20)

    country: Optional[str] = Field(default=None, max_length=100)

    is_default: Optional[bool] = None


# =========================================================
# ADDRESS RESPONSE
# =========================================================

class AddressResponse(BaseModel):
    """
    Standard response schema for user address.
    """

    id: int
    user_id: int

    label: Optional[str]

    full_name: str
    phone_number: str

    address_line1: str
    address_line2: Optional[str]

    city: str
    state: str
    postal_code: str
    country: str

    is_default: bool

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# ADDRESS LIST RESPONSE
# =========================================================

class AddressListResponse(BaseModel):
    """
    Paginated response for listing addresses.
    """

    total: int
    page: int
    limit: int

    items: list[AddressResponse]