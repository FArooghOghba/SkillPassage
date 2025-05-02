"""Auth services module provides password hashing and token functions.

This module contains functions and utilities for handling password hashing,
verification, and token-based authentication using bcrypt and OAuth2.
"""
from passlib.context import CryptContext


# Configure bcrypt for password hashing
pass_hash_bcrypt_context = CryptContext(
    schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=12
)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt with salt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Securely hashed password with salt

    Note:
        Uses bcrypt with a work factor of 12 for optimal security/performance
    """
    password_hash = pass_hash_bcrypt_context.hash(password)
    return password_hash


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Securely verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password to verify against

    Returns:
        bool: True if password matches hash, False otherwise

    Note:
        Uses constant-time comparison to prevent timing attacks
    """
    password_verified = pass_hash_bcrypt_context.verify(
        plain_password, hashed_password
    )
    return password_verified
