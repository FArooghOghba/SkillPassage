"""User-related constants and enums."""
from enum import Enum


class UserType(str, Enum):
    """
    User type enumeration.

    Defines the possible types of users in the system.
    """

    ADMIN = "admin"
    PROFESSIONAL = "professional"
    CLIENT = "client"
