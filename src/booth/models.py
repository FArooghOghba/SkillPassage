"""Booth-related database models."""
from typing import TYPE_CHECKING
from uuid import (
    UUID,
    uuid4,
)

from sqlalchemy import (
    ARRAY,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.booth.constants import BoothStatus
from src.db.base import BaseModel


if TYPE_CHECKING:
    from src.user.models import User


class Booth(BaseModel):
    """SQLAlchemy model representing a Professional's virtual booth.

    A Booth acts as a professional's dedicated space on the platform to
    showcase their skills, services, and portfolio to potential clients.
    The visibility of a booth is controlled by both an administrative status
    and a user-controlled publishing flag.

    Attributes:
        id: The unique identifier for the booth.
        owner_id: The foreign key linking to the User who owns this booth.
        title: A short, descriptive title for the booth (e.g., "Expert Web
               Development Services").
        description: A detailed, long-form description of the services
                     offered, professional background, etc. Uses the Text
                     type for flexibility.
        tags: A list of searchable keywords or tags that help clients discover
              this booth (e.g., ["python", "fastapi", "Vue.js"]).
        status: The administrative moderation status of the booth
                (e.g., PENDING, APPROVED, SUSPENDED), controlled by platform
                admins.
        is_published: A boolean flag controlled by the professional (owner) to
                      make their booth live or take it down temporarily.
                      A booth is only visible to the public if its status
                      is 'APPROVED' and it is_published is True.
        owner: The ORM relationship to the User object who owns the booth.
    """

    __tablename__ = "booths"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    owner_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey(column="users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(length=120),
        nullable=False,
        index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)),
        nullable=True
    )
    status: Mapped[BoothStatus] = mapped_column(
        SQLAlchemyEnum(
            BoothStatus, name="booth_status_enum", native_enum=True
        ),
        default=BoothStatus.PENDING,
        nullable=False,
        index=True
    )
    is_published: Mapped[bool] = mapped_column(default=False, nullable=False)
    owner: Mapped["User"] = relationship(
        back_populates="booths",
        lazy="selectin"  # Eagerly load the owner details with the booth
    )

    def __str__(self) -> str:
        """Return string representation of the booth."""
        return f"Booth: {self.title}"

    def __repr__(self) -> str:
        """Return detailed string representation of the booth."""
        return f"<Booth {self.title} ({self.id})>"
