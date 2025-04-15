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

    def __init__(
        self,
        identifier: UUID | str | None = None,  # Accept UUID, string, or None
        lookup_field: str = "ID"  # Specify which field was used
    ) -> None:
        """
        Initialize user not found error.

        Args:
            identifier: The value (ID, email, username, etc.)
            used for the lookup.
            lookup_field: The name of the field used for the lookup
            (e.g., "ID", "Email").
        """
        # Create a user-friendly string representation of the identifier
        id_str = str(identifier) if identifier is not None else "unknown"

        # Construct a dynamic detail message
        message = f"User not found with {lookup_field}: {id_str}"

        # Call the parent __init__ with the standard 404 code
        # and dynamic message
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail=message
        )

    def __str__(self) -> str:
        """
        Provide a string representation useful for direct assertion in tests.

        Example: "404: User not found with Email: test@example.com"
        """
        # Matches the format often asserted using str(exc_info.value)
        return f"{self.status_code}: {self.detail}"
