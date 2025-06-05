"""User-related database models."""
from datetime import datetime
from uuid import (
    UUID,
    uuid4,
)

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.db.base import BaseModel


class User(BaseModel):
    """SQLAlchemy model representing a user in the system.

    Inherits from BaseModel to include created_at and updated_at timestamps.
    Includes authentication fields, user status flags, and a one-to-one
    relationship with BaseUserProfile.
    """
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(length=320),
        unique=True,
        nullable=False,
        index=True
    )
    username: Mapped[str] = mapped_column(
        String(length=64),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Relationship to profile
    profile: Mapped["BaseUserProfile"] = relationship(
        argument="BaseUserProfile",
        back_populates="user",  # access user from profile via profile.user
        uselist=False,  # ensures a user has exactly one profile (one-to-one)
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            sqltext="length(username) >= 3", name="username_min_length"
        ),
    )

    def __str__(self) -> str:
        """Return string representation of the user."""
        return f"User: {self.username}"

    def __repr__(self) -> str:
        """Return detailed string representation of the user."""
        return f"<User {self.username} ({self.id})>"


class BaseUserProfile(BaseModel):
    """SQLAlchemy model representing a user's base profile information.

    Inherits from BaseModel to include created_at and updated_at timestamps.
    Contains core profile fields and maintains a one-to-one relationship
    with User. Can be extended with additional profile types like
    ProfessionalProfileExtension.
    """
    __tablename__ = "user_profiles_base"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey(column="users.id", ondelete="CASCADE"),
        unique=True,  # Ensures one-to-one relationship
        nullable=False  # Every profile must have a user
    )
    first_name: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False
    )
    phone_number: Mapped[str | None] = mapped_column(
        String,
    )

    # Relationship to user
    user: Mapped[User] = relationship(
        argument="User",
        back_populates="profile"
    )

    # Links to extension tables
    professional_extension: Mapped["ProfessionalProfileExtension | None"] = \
        relationship(
            argument="ProfessionalProfileExtension",
            back_populates="base_profile",
            uselist=False,
            cascade="all, delete-orphan"
        )

    __table_args__ = (
        CheckConstraint(
            sqltext="length(first_name) >= 2", name="first_name_min_length"
        ),
        CheckConstraint(
            sqltext="length(last_name) >= 2", name="last_name_min_length"
        ),
    )

    def __str__(self) -> str:
        """Return string representation of the user profile."""
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        """Return the user's full name by combining first and last name.

        Returns:
            str: The user's full name in 'first_name last_name' format.
        """
        return f"{self.first_name} {self.last_name}"


class ProfessionalProfileExtension(BaseModel):
    """Pro profile extension model for users applying to become professionals.

    Stores additional professional information, application status,
    and approval workflow data for users seeking professional privileges
    in the system.
    """
    __tablename__ = "user_profiles_professional_extensions"

    base_profile_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey(column="user_profiles_base.id", ondelete="CASCADE"),
        primary_key=True
    )

    specialization: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    bio: Mapped[str | None] = mapped_column(String, nullable=True)
    years_of_experience: Mapped[int | None] = mapped_column(nullable=True)

    is_application_approved: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    approved_by_admin_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )  # Link to admin who approved
    approved_by_admin: Mapped["User | None"] = relationship(
        argument="User",
        foreign_keys=[approved_by_admin_id]
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active_as_professional: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Can be deactivated later

    base_profile: Mapped["BaseUserProfile"] = relationship(
        argument="BaseUserProfile",
        back_populates="professional_extension"
    )
