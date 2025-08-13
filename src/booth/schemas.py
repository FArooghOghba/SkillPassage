"""Pydantic schemas for booth-related data validation and serialization.

This module defines the schema classes used for validating and serializing
booth data throughout the application. It includes schemas for various
booth-related operations such as booth creation, updates, and API responses.
"""
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from src.booth.constants import BoothStatus
from src.user.schemas.user_schemas import User as UserResponseSchema


class BoothBase(BaseModel):
    """Base schema for booth data validation.

    This schema defines the common fields and validation rules shared across
    different booth-related operations. It provides the most basic fields
    required for a booth, such as the title, description, and tags.
    """

    title: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="A short, descriptive title for the booth."
    )
    description: str | None = Field(
        default=None,
        max_length=512,
        description="A detailed description of the services offered."
    )
    tags: list[str] | None = Field(
        default=None,
        description="A list of searchable keywords or tags.",
        max_length=10
    )


class BoothCreate(BoothBase):
    """Schema for creating a new booth. Sent by a professional user.

    This schema defines the fields required for creating a new booth, which
    are typically sent by a professional user. It includes the title,
    description, and tags.
    """
    # Inherits title, description, tags.
    # The owner_id will be taken from the authenticated user in the endpoint.
    # Default status and is_published are set by the ORM model.
    pass


class BoothUpdate(BaseModel):
    """Schema for a professional updating their OWN booth.

    This schema defines the fields that a professional user can update for
    their own booth. All fields are optional, and the update endpoint will
    only change the fields that are provided in the request.
    """

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=120,
        description="A short, descriptive title for the booth."
    )
    description: str | None = Field(
        default=None,
        description="A detailed description of the services offered."
    )
    tags: list[str] | None = Field(
        default=None,
        description="A list of searchable keywords or tags.",
        max_length=10
    )
    is_published: bool | None = Field(
        default=None,
        description="Set to true to make the booth public (if approved), "
                    "false to hide it."
    )


class BoothAdminUpdate(BaseModel):
    """Schema for an admin updating a booth's status or moderation info.

    This schema defines the fields that an administrator can update for
    a booth, such as its moderation status or approval status.
    """

    status: BoothStatus | None = Field(
        default=None,
        description="The administrative moderation status of the booth."
    )
    # If admins can also edit content, this could inherit from BoothUpdate.


class BoothResponse(BoothBase):
    """Schema for representing a Booth in API responses.

    This schema is used to serialize booth data for API responses that
    return booth information. It includes all public information about a
    booth, such as its title, description, tags, status, and owner
    information.
    """

    id: UUID
    status: BoothStatus
    is_published: bool

    # Nest the owner's information.
    # We use the UserResponseSchema which is the public-facing user schema.
    owner: UserResponseSchema

    # Important: This allows Pydantic to create this schema from
    # an ORM model instance.
    model_config = ConfigDict(from_attributes=True)


BoothResponse.model_rebuild()
