"""Booth-related constants and enums."""
from enum import Enum


class BoothStatus(str, Enum):
    """Represents the administrative status of a Booth.

    This status is typically controlled by platform administrators
    and is used for moderation and quality control. It is distinct
    from the professional-controlled `is_published` flag on the Booth model.

    Attributes:
        PENDING: The booth has been created by a professional but is awaiting
                 admin review and approval before it can be made public.
                 This is the default status for new booths.
        APPROVED: The booth has been reviewed and approved by an admin.
                  It can be made visible to the public if the professional
                  sets its `is_published` flag to True.
        SUSPENDED: The booth has been taken down by an administrator due to a
                   violation of terms or other issues. It is not visible to
                   the public, regardless of its `is_published` status.
    """

    APPROVED = "approved"
    PENDING = "pending"
    SUSPENDED = "suspended"
