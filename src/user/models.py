"""User-related database models."""
from uuid import (
    UUID,
    uuid4,
)

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from src.db.base import BaseModel


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
        return f"User: {self.username}"

    def __repr__(self) -> str:
        """Return detailed string representation of the user."""
        return f"<User {self.username} ({self.id})>"
