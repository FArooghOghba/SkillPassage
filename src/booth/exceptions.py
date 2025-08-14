"""Booth domain specific exceptions."""
from uuid import UUID

from fastapi import status

from src.core.exceptions import BaseAPIError


class BoothError(BaseAPIError):
    """Base exception for booth-related errors."""
    pass


class BoothNotFoundError(BoothError):
    """Exception raised when a requested booth is not found."""

    def __init__(self, booth_id: UUID):
        """Initialize booth not found error."""
        detail = f"Booth not found with ID: {booth_id}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BoothUpdateForbiddenError(BoothError):
    """Exception raised when a user attempts to update a booth they don't own.

    This exception is raised when a user attempts to update a booth that they
    do not own. This can happen if a user attempts to update a booth that
    another user created, or if a user attempts to update a booth that has
    been created by an administrator.
    """

    def __init__(self, user_id: UUID, booth_id: UUID):
        """Initialize booth update forbidden error."""
        detail = (
            f"User {user_id} does not have permission "
            f"to update booth {booth_id}."
        )
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BoothCreationError(BoothError):
    """Base for errors that occur during booth creation."""
    pass


class BoothOwnerInactiveError(BoothCreationError):
    """Exception raised when an inactive user attempts to create a booth."""

    def __init__(self, user_id: UUID):
        """Initialize inactive owner error."""
        detail = f"User {user_id} is inactive and cannot create a booth."
        # 403 Forbidden is a good choice here as it's an authorization issue.
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BoothOwnerNotProfessionalError(BoothCreationError):
    """Exception raised when a non-pro user attempts to create a booth.

    This exception is raised when a user attempts to create a booth without
    having an approved professional status. This can happen if a user attempts
    to create a booth without filling out their professional profile or
    if their professional status has not been approved by an administrator.
    """

    def __init__(self, user_id: UUID):
        """Initialize not a professional error."""
        detail = (
            f"User {user_id} is not an approved professional and "
            f"cannot create a booth."
        )
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# Note: We don't need a `BoothAlreadyExistsError` because
# a user can have multiple booths. If you decide to limit users to one booth,
# then you would create this exception and handle the IntegrityError on a
# (owner_id) unique constraint.
