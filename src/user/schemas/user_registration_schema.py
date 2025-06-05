"""Pydantic schema for validating user registration requests.

This module defines a single schema `RegisterUserRequest` that
combines the fields for user creation and profile creation, and
includes a validator to check if the provided passwords match.

"""
from pydantic import (
    Field,
    model_validator,
)

from src.user.schemas.user_base_profile_schemas import UserBaseProfileCreate
from src.user.schemas.user_schemas import UserCreate


class RegisterUserRequest(UserCreate, UserBaseProfileCreate):
    """Schema representing the request body for user registration.

    Combines user creation fields (email, username, password) and
    profile creation fields (first_name, last_name, phone_number).
    Includes password validation.
    """
    # Inherits email, username, password (with complexity validation)
    # Inherits first_name, last_name, phone_number

    # Add the confirmation field
    password_confirm: str = Field(description="Password confirmation")

    # Add a validator to check if passwords match
    @model_validator(mode='after')
    def check_passwords_match(self) -> 'RegisterUserRequest':
        """Validator to check if the two passwords match.

        Raises a ValueError if the two passwords provided
        (password and password_confirm) are not the same.

        Returns the validated model instance.
        """
        pw1 = self.password
        pw2 = self.password_confirm
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('Passwords do not match')
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "new.user@example.com",
                    "username": "new_user_123",
                    "password": "ValidPassword123!",
                    "password_confirm": "ValidPassword123!",
                    "first_name": "New",
                    "last_name": "User",
                    "phone_number": "+15551234567",
                }
            ]
        }
    }
