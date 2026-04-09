"""
User Schemas

Defines request and response models
for user profile management APIs.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from datetime import date
from enum import Enum


# ==========================================================
# USER PROFILE RESPONSE
# ==========================================================

class UserProfileResponse(BaseModel):

    id: int
    email: EmailStr
    phone: str
    role: str
    status: str
    full_name: Optional[str]
    gender: Optional[str]
    date_of_birth: Optional[date]
    
    class Config:
        from_attributes = True



# ==========================================================
# UPDATE PROFILE REQUEST
# ==========================================================

class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class UpdateProfileRequest(BaseModel):

    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    gender: Optional[GenderEnum]
    date_of_birth: Optional[date] = None

# ==========================================================
# SESSION RESPONSE
# ==========================================================

class SessionResponse(BaseModel):

    id: int
    ip_address: str
    user_agent: str
    created_at: datetime