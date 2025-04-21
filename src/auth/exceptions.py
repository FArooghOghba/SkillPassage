"""Authentication and authorization related exceptions.

This module defines a hierarchy of exceptions for handling various
authentication and authorization scenarios in the application.
"""
from fastapi import status

from src.core.exceptions import BaseAPIError


class AuthError(BaseAPIError):
    """Base exception for authentication/authorization errors.

    Serves as the parent class for all auth-related exceptions,
    providing consistent error handling and response formatting.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        headers: dict[str, str] | None = None
    ) -> None:
        """Initialize authentication error.

        Args:
            message: Error message
            status_code: HTTP status code (default: 401)
            headers: Optional response headers
        """
        super().__init__(
            status_code=status_code,
            detail=message,
            headers=headers
        )


class NotAuthorizedError(AuthError):
    """Exception for authentication failures.

    Raised when a user is not properly authenticated, typically due to:
    - Missing authentication credentials
    - Expired authentication token
    - Invalid authentication token format
    """

    def __init__(
        self,
        message: str = "Not authenticated",
        headers: dict[str, str] | None = None
    ) -> None:
        """Initialize not authenticated error.

        Args:
            message: Custom error message (defaults to "Not authenticated")
            headers: Optional response headers (e.g., WWW-Authenticate)

        Note:
            Automatically adds WWW-Authenticate: Bearer header as per RFC 7235
        """
        # Add WWW-Authenticate header for 401 responses as per RFC 7235
        headers = headers or {"WWW-Authenticate": "Bearer"}
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers=headers
        )


class ForbiddenError(AuthError):
    """Exception for authorization failures.

    Raised when an authenticated user lacks the required permissions
    to access a resource or perform an action.
    """

    def __init__(
        self,
        message: str = "Permission denied",
        headers: dict[str, str] | None = None
    ) -> None:
        """Initialize forbidden error.

        Args:
            message: Custom error message
            headers: Optional response headers
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            headers=headers
        )


class TokenError(AuthError):
    """Exception for JWT token-specific errors.

    Raised for issues related to token handling:
    - Malformed tokens
    - Invalid signatures
    - Missing required claims
    """

    def __init__(
        self,
        message: str = "Invalid token",
        headers: dict[str, str] | None = None
    ) -> None:
        """Initialize token error.

        Args:
            message: Custom error message (defaults to "Invalid token")
            headers: Optional response headers

        Note:
            Automatically adds WWW-Authenticate: Bearer header
            for 401 responses
        """
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )
