"""Pydantic schemas for user-related data validation and serialization.

This module defines the schema classes used for validating and serializing
user data throughout the application. It includes schemas for various
user-related operations such as user creation, updates, and API responses.
"""
from typing import Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from src.user.schemas.user_base_profile_schemas import (
    UserBaseProfile as UserBaseProfileSchema,
)
from src.user.schemas.user_professional_profile_schemas import (
    UserProfessionalProfile as UserProfessionalProfileSchema,
)
from src.user.utils import PasswordValidationMixin


class UserBase(BaseModel):
    """Base schema for user data validation.

    This schema defines the common fields and validation rules shared across
    different user-related operations.

    Attributes:
        email: User's email address, validated using EmailStr.
        username: Alphanumeric username (including - and _).
    """

    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=64,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Alphanumeric username with optional "
                    "underscores and hyphens"
    )


class UserCreate(UserBase, PasswordValidationMixin):
    """Schema for user creation requests.

    Extends UserBase to include password field for new user registration.
    Inherits all validation rules from UserBase.

    Attributes:
        password: Plain text password (will be hashed before storage).
    """

    password: str = Field(
        description="User's password in plain text"
    )


class UserUpdate(BaseModel):
    """Schema for user update requests.

    Similar to UserBase but all fields are optional to allow partial
    updates.

    Attributes:
        All fields are optional versions of UserBase fields.
    """

    email: EmailStr | None = None
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Alphanumeric username with optional"
                    "underscores and hyphens"
    )


class UserInDB(UserBase):
    """Schema representing user data as stored in the database.

    Extends UserBase to include database-specific fields. Used internally
    for database operations and should not be exposed to API clients.

    Attributes:
        id: Unique identifier for the user.
        is_active: Flag indicating if the user account is active.
        hashed_password: Securely hashed version of the user's password.
    """

    id: UUID
    is_active: bool = True
    is_superuser: bool = False
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    """Schema for user data in API responses.

    Public-facing user schema that excludes sensitive information.
    Used for API responses when returning user data to clients.

    Attributes:
        id: Unique identifier for the user.
        is_active: Flag indicating if the user account is active.
    """

    id: UUID
    is_active: bool = True
    is_superuser: bool

    profile: UserBaseProfileSchema
    professional_profile: Optional[UserProfessionalProfileSchema] = None

    model_config = ConfigDict(from_attributes=True)
