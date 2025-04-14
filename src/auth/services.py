"""
Authentication services module provides password hashing and token functions.

This module contains functions and utilities for handling password hashing,
verification, and token-based authentication using bcrypt and OAuth2.
"""

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext


oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

# Password hashing context
pass_hash_bcrypt_context = CryptContext(
    schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=12
)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password
    """
    password_hash = pass_hash_bcrypt_context.hash(password)
    return password_hash  # type: ignore[no-any-return]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against

    Returns:
        bool: True if password matches hash, False otherwise
    """
    password_verified = pass_hash_bcrypt_context.verify(
        plain_password, hashed_password
    )
    return password_verified  # type: ignore[no-any-return]
