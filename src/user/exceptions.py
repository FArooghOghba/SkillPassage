"""Exception classes for handling various user operation errors."""

from typing import Any
from uuid import UUID

from fastapi import (
    HTTPException,
    status,
)


class UserError(HTTPException):  # type: ignore[misc]
    """Base exception for user-related errors."""

    def __init__(
            self, status_code: int = status.HTTP_400_BAD_REQUEST,
            detail: Any = None
    ) -> None:
        """
        Initialize the base user error.

        Args:
            status_code: HTTP status code
            detail: Error detail message
        """
        super().__init__(status_code=status_code, detail=detail)


class UserNotFoundError(UserError):
    """Exception raised when a requested user is not found."""

    def __init__(self, user_id: UUID | None = None) -> None:
        """
        Initialize user not found error.

        Args:
            user_id: UUID of the user that was not found
        """
        message = f"User not found with ID: {user_id}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail=message
        )
