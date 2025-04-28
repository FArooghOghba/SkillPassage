"""Pydantic schemas for user-related data validation and serialization.

This module defines the schema classes used for validating and serializing
user data throughout the application. It includes schemas for various
user-related operations such as user creation, updates, and API responses.
"""
import re
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


# Define password requirements clearly
REQUIRED_LOWERCASE = True
REQUIRED_UPPERCASE = True
REQUIRED_DIGIT = True
REQUIRED_SPECIAL = True

# Define allowed special characters clearly if using regex check
SPECIAL_CHARS_REGEX = r"[@$!%*?&_^)(#\-]"

# Length check
MIN_PASSWORD_LENGTH = 8


class UserBase(BaseModel):
    """Base schema for user data validation.

    This schema defines the common fields and validation rules shared across
    different user-related operations.

    Attributes:
        email: User's email address, validated using EmailStr.
        username: Alphanumeric username (including - and _).
    """

    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=64,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Alphanumeric username with optional "
                    "underscores and hyphens"
    )


class UserCreate(UserBase):
    """Schema for user creation requests.

    Extends UserBase to include password field for new user registration.
    Inherits all validation rules from UserBase.

    Attributes:
        password: Plain text password (will be hashed before storage).
    """

    password: str = Field(
        description="User's password in plain text"
    )

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, password: str) -> str:
        """Validate user password complexity.

        Checks the password against the following rules:

        - Minimum length
        - Uppercase letter
        - Lowercase letter
        - Digit
        - Special character (if using regex check)

        Raises ValueError if any of the rules are violated.

        Args:
            password (str): The password to validate

        Returns:
            str: The validated password
        """
        errors = []
        if len(password) < MIN_PASSWORD_LENGTH:
            errors.append(
                f"must be at least {MIN_PASSWORD_LENGTH} characters long"
            )
        if (REQUIRED_LOWERCASE and
                not re.search(pattern=r"[a-z]", string=password)):
            errors.append("must contain a lowercase letter")
        if (REQUIRED_UPPERCASE and
                not re.search(pattern=r"[A-Z]", string=password)):
            errors.append("must contain an uppercase letter")
        if (REQUIRED_DIGIT and
                not re.search(pattern=r"\d", string=password)):
            errors.append("must contain a digit")
        if (REQUIRED_SPECIAL and
                not re.search(pattern=SPECIAL_CHARS_REGEX, string=password)):
            errors.append(
                f"must contain a special character ({SPECIAL_CHARS_REGEX})"
            )

        if errors:
            # Combine errors for a single clear message
            raise ValueError(
                f"Password validation failed: {'; '.join(errors)}"
            )

        return password


class UserUpdate(BaseModel):
    """Schema for user update requests.

    Similar to UserBase but all fields are optional to allow partial
    updates.

    Attributes:
        All fields are optional versions of UserBase fields, plus password.
    """

    email: EmailStr | None = None
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Alphanumeric username with optional"
                    "underscores and hyphens"
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=64,
        description="New password in plain text"
    )


class UserInDB(UserBase):
    """Schema representing user data as stored in the database.

    Extends UserBase to include database-specific fields. Used internally
    for database operations and should not be exposed to API clients.

    Attributes:
        id: Unique identifier for the user.
        is_active: Flag indicating if the user account is active.
        hashed_password: Securely hashed version of the user's password.
    """

    id: UUID
    is_active: bool = True
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    """Schema for user data in API responses.

    Public-facing user schema that excludes sensitive information.
    Used for API responses when returning user data to clients.

    Attributes:
        id: Unique identifier for the user.
        is_active: Flag indicating if the user account is active.
    """

    id: UUID
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
