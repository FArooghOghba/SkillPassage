"""User-related database models."""
from uuid import (
    UUID,
    uuid4,
)

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum as SQLAlchemyEnum,
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
from src.user.constants import UserRole


class User(BaseModel):
    """User model for authentication and authorization."""

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

    # Relationship to profile
    profile: Mapped["UserProfile"] = relationship(
        argument="UserProfile",
        back_populates="user",  # access user from profile via profile.user
        uselist=False  # ensures one user has exactly one profile (one-to-one)
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


class UserProfile(BaseModel):
    """Profile model for user personal information."""

    __tablename__ = "user_profiles"

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
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole, name="user_role_enum", native_enum=True),
        default=UserRole.CLIENT.value,
        nullable=False,
    )

    # Relationship to user
    user: Mapped[User] = relationship(
        argument="User",
        back_populates="profile"
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
