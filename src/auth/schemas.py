"""Authentication-related Pydantic schemas.

This module defines schemas for authentication and authorization,
including access tokens, refresh tokens, and token payloads.
"""
from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class Token(BaseModel):
    """Schema for API authentication token response.

    This schema represents the token data returned to clients
    after successful authentication.

    Attributes:
        access_token: JWT token for accessing protected endpoints.
        token_type: Type of token (always "bearer").
        expires_in: Timestamp when the token will expire.
        refresh_token: Optional token for refreshing the access token.
    """

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Access token lifetime in seconds")
    refresh_token: str | None = Field(
        default=None,
        description="Refresh token for obtaining new access tokens"
    )


class TokenPayload(BaseModel):
    """Schema for JWT token payload.

    This schema represents the data encoded within the JWT token.
    Used internally for token creation and validation.

    Attributes:
        sub: Subject of the token (user ID).
        exp: Expiration timestamp.
        iat: Issued at timestamp.
    """

    sub: UUID = Field(description="User ID (subject)")
    exp: datetime = Field(description="Token expiration timestamp")
    iat: datetime = Field(description="Token issued at timestamp")


class TokenRefresh(BaseModel):
    """Schema for token refresh requests.

    This schema validates refresh token requests from clients.

    Attributes:
        refresh_token: The refresh token previously issued to the client.
    """

    refresh_token: str = Field(description="Valid refresh token")


class EmailPasswordLoginRequest(BaseModel):
    """Schema for user login requests using email and password.

    This schema represents the data sent by the client to authenticate
    a user.

    Attributes:
        email: User's email address.
        password: User's password.
    """

    email: EmailStr = Field(description="User's email address")
    password: str = Field(description="User's password")
