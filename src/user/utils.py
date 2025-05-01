"""Utility classes and functions for user-related operations.

This module contains utility mixins and helper functions that are used across
the user module, particularly for data validation and transformation.
"""
import re

from pydantic import field_validator


# Define password requirements clearly
REQUIRED_LOWERCASE = True
REQUIRED_UPPERCASE = True
REQUIRED_DIGIT = True
REQUIRED_SPECIAL = True

# Define allowed special characters clearly if using regex check
SPECIAL_CHARS_REGEX = r"[@$!%*+?&_^)(#\-]"

# Length check
MIN_PASSWORD_LENGTH = 8


class PhoneNumberMixin:
    """Mixin class providing phone number validation functionality.

    This mixin can be used with Pydantic models to add standardized phone
    number validation.
    It ensures phone numbers follow the E.164 format and contain only
    valid characters.

    Features:
        - Strips spaces and hyphens from phone numbers
        - Ensures the '+' prefix is present
        - Validates that the number contains only digits after the '+' prefix
    """

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str | None) -> str | None:
        """Validate and normalize phone number format.

        Args:
            v: The phone number string to validate, or None.

        Returns:
            str | None: The normalized phone number or None if input is None.

        Raises:
            ValueError: If the phone number format is invalid, with a specific
                message describing the error.

        Examples:
            >>> PhoneNumberMixin.validate_phone_number("123456789")
            "+123456789"
            >>> PhoneNumberMixin.validate_phone_number("+1-234-567-89")
            "+123456789"
            >>> PhoneNumberMixin.validate_phone_number(None)
            None
        """
        if v is None:
            return None

        # Remove any spaces or hyphens
        v = v.replace(" ", "").replace("-", "")

        # Check for non-digit characters (except the "+" prefix)
        stripped = v.replace("+", "") if v.startswith("+") else v
        if not stripped.isdigit():
            invalid_chars = [char for char in stripped if not char.isdigit()]
            raise ValueError(
                f"Invalid phone number format: contains non-digit characters "
                f"({', '.join(set(invalid_chars))}). "
                f"Phone number must follow E.164 format: "
                f"+[country code][number]"
            )

        # Add + prefix if missing
        if not v.startswith("+"):
            v = "+" + v

        # Check minimum/maximum length requirements

        # +[country code (1-3 digits)][number (at least 2 digits)]
        if len(v) < 6:
            raise ValueError(
                "Invalid phone number: too short. "
                "Phone number must follow E.164 format: "
                "+[country code][number]"
            )

        # +[country code (1-3 digits)][number (up to 12 digits)]
        if len(v) > 16:
            raise ValueError(
                "Invalid phone number: too long. "
                "Phone number must follow E.164 format: "
                "+[country code][number]"
            )

        return v


class PasswordValidationMixin:
    """Mixin providing password validation functionality."""

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
