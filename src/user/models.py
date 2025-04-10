"""User-related database models."""
from uuid import (
    UUID as _UUID,
    uuid4,
)

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum as SQLAlchemyEnum,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from src.db.base import BaseModel
from src.user.constants import UserType


class User(BaseModel):
    """User model for storing user-related data."""

    __tablename__ = "users"

    id: Mapped[_UUID] = mapped_column(
        UUID(as_uuid=True),
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
    first_name: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False
    )
    phone_number: Mapped[str | None] = mapped_column(String)
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024),
        nullable=False,
    )
    type: Mapped[UserType] = mapped_column(
        SQLAlchemyEnum(UserType, name="user_type_enum", native_enum=True),
        default=UserType.CLIENT,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            sqltext="length(username) >= 3", name="username_min_length"
        ),
        CheckConstraint(
            sqltext="length(first_name) >= 2", name="first_name_min_length"
        ),
        CheckConstraint(
            sqltext="length(last_name) >= 2", name="last_name_min_length"
        ),
    )

    def __str__(self) -> str:
        """Return string representation of the user."""
        return f"{self.first_name} {self.last_name} ({self.username})"

    def __repr__(self) -> str:
        """Return detailed string representation of the user."""
        return f"<User {self.username} ({self.id})>"
