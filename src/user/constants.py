"""User-related constants and enums."""
from enum import Enum


class UserRole(str, Enum):
    """Enumeration of possible user roles in the system.

    Defines the available roles that can be assigned to users,
    controlling their permissions and access levels.
    """

    ADMIN = "admin"
    PROFESSIONAL = "professional"
    CLIENT = "client"
