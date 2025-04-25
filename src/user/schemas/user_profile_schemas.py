"""Pydantic schemas for user profile data validation and serialization."""

from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from src.user.constants import UserRole
from src.user.utils import PhoneNumberMixin


class UserProfileBase(BaseModel, PhoneNumberMixin):
    """Base schema for user profile data validation.

    This schema defines the common fields and validation rules shared across
    different profile-related operations.

    Attributes:
        first_name: User's first name (2-50 characters).
        last_name: User's last name (2-50 characters).
        phone_number: Optional phone number in E.164 format.
        role: User's role in the system (default: CLIENT).
    """

    first_name: str = Field(
        min_length=2,
        max_length=50,
        description="User's first name"
    )
    last_name: str = Field(
        min_length=2,
        max_length=50,
        description="User's last name"
    )
    phone_number: str | None = Field(
        default=None,
        max_length=20,
        pattern=r"^\+?[1-9]\d{1,14}$",
        description="Phone number in E.164 format: +[country code][number]"
    )
    role: str = Field(
        default=UserRole.CLIENT.value,
        description="User's role in the system"
    )


class UserProfileCreate(UserProfileBase):
    """Schema for profile creation requests.

    Inherits all fields from UserProfileBase. Used when creating
    a new profile for a user.
    """
    pass


class UserProfileUpdate(BaseModel):
    """Schema for profile update requests.

    Similar to UserProfileBase but all fields are optional to allow
    partial updates.

    Attributes:
        All fields are optional versions of UserProfileBase fields.
    """

    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="User's first name"
    )
    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="User's last name"
    )
    phone_number: str | None = Field(
        default=None,
        max_length=20,
        pattern=r"^\+?[1-9]\d{1,14}$",
        description="Phone number in E.164 format: +[country code][number]"
    )
    role: UserRole | None = Field(
        default=None,
        description="User's role in the system"
    )


class UserProfile(UserProfileBase):
    """Schema for profile data in API responses.

    Extends UserProfileBase to include database-specific fields.
    Used for API responses when returning profile data to clients.

    Attributes:
        id: Unique identifier for the profile.
        user_id: ID of the associated user.
    """

    id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)
