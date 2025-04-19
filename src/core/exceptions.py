"""Base exception classes for the application."""

from typing import Any

from fastapi import (
    HTTPException,
    status,
)


class BaseAPIError(HTTPException):
    """Base exception for all API errors."""

    def __init__(
            self,
            status_code: int = status.HTTP_400_BAD_REQUEST,
            detail: Any = None,
            headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the base API error.

        Args:
            status_code: HTTP status code
            detail: Error detail message
            headers: Optional response headers
        """
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers,
        )
