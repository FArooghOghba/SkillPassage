"""
Utility classes and functions for user-related operations.

This module contains utility mixins and helper functions that are used across
the user module, particularly for data validation and transformation.
"""
from pydantic import field_validator


class PhoneNumberMixin:
    """
    Mixin class providing phone number validation functionality.

    This mixin can be used with Pydantic models to add standardized phone
    number validation.
    It ensures phone numbers follow the E.164 format and contain only
    valid characters.

    Features:
        - Strips spaces and hyphens from phone numbers
        - Ensures the '+' prefix is present
        - Validates that the number contains only digits after the '+' prefix
    """

    @classmethod
    @field_validator("phone_number")
    def validate_phone_number(cls, v: str | None) -> str | None:
        """
        Validate and normalize phone number format.

        Args:
            v: The phone number string to validate, or None.

        Returns:
            str | None: The normalized phone number or None if input is None.

        Raises:
            ValueError: If the phone number contains non-digit characters
                (excluding the '+' prefix).

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

        # Add + prefix if missing
        if not v.startswith("+"):
            v = "+" + v

        if not v.replace("+", "").isdigit():
            raise ValueError("Phone number must contain only digits")

        return v
