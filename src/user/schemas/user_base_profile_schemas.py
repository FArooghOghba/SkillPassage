"""Pydantic schemas for user profile data validation and serialization."""

from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from src.user.utils import PhoneNumberMixin


class UserBaseProfileBase(BaseModel, PhoneNumberMixin):
    """Base schema for user base profile data validation.

    This schema defines the common fields and validation rules shared across
    different profile-related operations.

    Attributes:
        first_name: User's first name (2-50 characters).
        last_name: User's last name (2-50 characters).
        phone_number: Optional phone number in E.164 format.
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
        description="Phone number in E.164 format: +[country code][number]"
    )


class UserBaseProfileCreate(UserBaseProfileBase):
    """Schema for base profile creation requests.

    Inherits all fields from UserProfileBase. Used when creating
    a new profile for a user.
    """
    pass


class UserBaseProfileUpdate(BaseModel, PhoneNumberMixin):
    """Schema for base profile update requests.

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
        description="Phone number in E.164 format: +[country code][number]"
    )


class UserBaseProfile(UserBaseProfileBase):
    """Schema for base profile data in API responses.

    Extends UserProfileBase to include database-specific fields.
    Used for API responses when returning profile data to clients.

    Attributes:
        id: Unique identifier for the profile.
        user_id: ID of the associated user.
    """

    id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)
