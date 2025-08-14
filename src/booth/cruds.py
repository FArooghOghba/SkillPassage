"""Contains FastAPI CRUD functions for Booth-related database operations.

This module contains the FastAPI endpoint functions that perform CRUD
operations on the Booth model. These functions are responsible for
validating the input data, performing the actual database operations using
the SQLAlchemy ORM, and returning the result to the caller.

The functions in this module should not be used directly. Instead, they should
be used as handlers for FastAPI endpoints.
"""
import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.booth.models import Booth as BoothModel
from src.booth.schemas import BoothCreate as BoothCreateSchema


logger = logging.getLogger(__name__)


async def create_booth(
        db: AsyncSession, *, obj_in: BoothCreateSchema, owner_id: UUID
) -> BoothModel:
    """Creates a new Booth record in the database.

    Args:
        db: The SQLAlchemy async session.
        obj_in: A Pydantic schema with the booth creation data.
        owner_id: The UUID of the user who will own this booth.

    Returns:
        The newly created Booth ORM model instance.

    Raises:
        IntegrityError: If the owner_id does not exist(foreign key violation).
        DataError: If data violates schema constraints (e.g., title too long).
        SQLAlchemyError: For other database-related issues.
    """
    # Create new booth instance
    booth = BoothModel(
        owner_id=owner_id,
        title=obj_in.title,
        description=obj_in.description,
        tags=obj_in.tags,
        # Default values for 'status' and 'is_published'
        # are set by the model itself
    )

    try:
        # Add the booth to the session
        db.add(booth)
        # Flush to send the INSERT statement to the DB, check constraints
        # This is where database-level errors (like FK violations)
        # will be raised.
        await db.flush()
        # Refresh to load the generated ID/defaults back onto the booth object
        await db.refresh(booth)

        logger.info(
            msg="Successfully created booth",
            extra={
                "owner_id": str(booth.owner_id),
                "booth_id": str(booth.id),
                "title": booth.title,
            }
        )

        return booth

    except SQLAlchemyError as e:
        # For a low-level CRUD function, it's often best to let the specific
        # SQLAlchemy exception propagate up to the service layer. The service
        # layer can then decide how to handle it
        # (e.g., raise a custom exception).
        # We catch it here primarily to log it and ensure a rollback.

        await db.rollback()

        logger.error(
            msg="Database error during booth creation",
            extra={
                "owner_id": str(owner_id),
                "title": obj_in.title,
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )
        # Re-raise the original exception for the service layer to handle.
        raise
