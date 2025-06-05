"""User professional profile schema definitions.

This module contains Pydantic schema models for managing user professional
profiles with approval workflows and activity tracking. The schemas inherit
professional fields from base models and support automatic ORM object
creation with linked base_profile_id references.

Key Features:
- Professional profile data validation
- Approval status workflow management
- Activity tracking and timestamps
- ORM integration with automatic field linking
- Base model inheritance for shared professional fields

Classes:
- Professional profile schemas with validation rules
- Approval workflow status models
- Activity tracking schemas with datetime fields
"""
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ProfessionalProfileExtensionBase(BaseModel):
    """Base model for professional profile extension data.

    Defines optional fields for professional specialization, biography,
    and years of experience with appropriate validation constraints.
    """

    specialization: str | None = Field(
        None, max_length=255,
        description="The user's professional specialization."
    )
    bio: str | None = Field(
        None, description="A short biography or description of services."
    )
    years_of_experience: int | None = Field(
        None, ge=0, description="Years of professional experience."
    )


class ProfessionalApplicationCreate(ProfessionalProfileExtensionBase):
    """Schema for creating a new professional profile application.

    Inherits professional fields from the base model. The base_profile_id
    is automatically linked by the system during ORM object creation.
    """

    # Inherits specialization, bio, years_of_experience.
    # User provides these.
    # The 'base_profile_id' is linked by the system when
    # creating the ORM object.
    pass


class ProfessionalProfileUpdate(BaseModel):
    """Pydantic model for updating professional profile information.

    Inherits optional fields from ProfessionalProfileExtensionBase
    for partial updates.
    """

    # Allows updating any of the fields from ProfessionalProfileExtensionBase.
    # All fields are implicitly optional because they inherit
    # from a base where they are optional.
    # If you want to make some fields *required* for an update,
    # you'd redefine them here without "| None".
    pass


class ProfessionalProfileUpdateByAdmin(BaseModel):
    """Schema for admin updates to professional profiles.

    Allows administrators to update approval status, rejection reasons,
    and professional activity status for user professional profiles.
    """

    # What an admin can update (e.g., approval status)
    is_application_approved: bool | None = None
    rejection_reason: str | None = Field(
        None, max_length=1024,
        description="Reason for application rejection, if applicable."
    )
    is_active_as_professional: bool | None = None


class UserProfessionalProfile(ProfessionalProfileExtensionBase):
    """Schema for user professional profile with approval status and activity.

    Extends the base professional profile with approval workflow fields
    and professional activity status. Configured for ORM attribute mapping.
    """

    is_application_approved: bool
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    is_active_as_professional: bool

    model_config = ConfigDict(from_attributes=True)
