"""User domain specific exceptions."""
from uuid import UUID

from fastapi import status

from src.core.exceptions import BaseAPIError


class UserError(BaseAPIError):
    """Base exception for user-related errors."""


class UserNotFoundError(UserError):
    """Exception raised when a requested user is not found."""

    def __init__(
        self,
        identifier: UUID | str | None = None,
        lookup_field: str = "ID"
    ) -> None:
        """Initialize user not found error.

        Args:
            identifier: The value used for lookup (ID, email, username)
            lookup_field: The field used for lookup (default: "ID")
        """
        id_str = str(identifier) if identifier is not None else "unknown"
        detail = f"User not found with {lookup_field}: {id_str}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserAlreadyExistsError(UserError):
    """Exception raised when attempting to create a duplicate user."""

    def __init__(
        self,
        identifier: str,
        lookup_field: str = "ID"
    ) -> None:
        """Initialize duplicate user error.

        Args:
            identifier: The value that caused the conflict (email, username)
            lookup_field: The field that caused the conflict (default: "ID")
        """
        detail = f"User already exists with {lookup_field}: {identifier}"
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class UserInactiveError(UserError):
    """Exception raised when attempting to access an inactive user account."""

    def __init__(self, user_id: UUID) -> None:
        """Initialize inactive user error.

        Args:
            user_id: ID of the inactive user
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account {user_id} is inactive"
        )
