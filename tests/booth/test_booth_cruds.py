"""Tests for Booth CRUD functions."""
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.booth.constants import BoothStatus
from src.booth.cruds import create_booth
from src.booth.schemas import BoothCreate as BoothCreateSchema


if TYPE_CHECKING:
    from src.user.models import User as UserModel


@pytest.mark.asyncio
class TestCreateBoothCRUD:
    """Tests for creating a Booth.

    This test suite covers the `create_booth` CRUD function,
    which is responsible for inserting a new Booth into the database.
    """

    async def test_create_booth_return_success(
            self, db_session: AsyncSession,
            first_test_client_user: "UserModel",
            first_test_booth_payload: dict[str, str]
    ) -> None:
        """Test that creating a Booth with valid data works correctly.

        This test verifies that the CRUD function correctly inserts a Booth
        into the database and returns the created Booth ORM model instance.
        """
        booth_data = BoothCreateSchema(**first_test_booth_payload)
        owner_id = first_test_client_user.id

        created_booth = await create_booth(
            db=db_session,
            obj_in=booth_data,
            owner_id=owner_id
        )

        # Verify booth attributes
        assert created_booth.id is not None
        assert created_booth.owner_id == owner_id
        assert created_booth.title == booth_data.title
        assert created_booth.description == booth_data.description
        assert created_booth.tags == booth_data.tags
        assert created_booth.status == BoothStatus.PENDING
        assert created_booth.is_published is False

    async def test_create_booth_with_minimal_data_return_success(
            self, db_session: AsyncSession,
            first_test_client_user: "UserModel"
    ) -> None:
        """Test that creating a Booth with minimal data works correctly.

        This test verifies that the CRUD function correctly inserts a Booth
        into the database and returns the created Booth ORM model instance,
        even with minimal data provided.
        """
        # 1. Prepare minimal data
        # (only title is required by BoothCreate schema)
        minimal_payload = {"title": "A Minimalist Booth"}
        booth_create_schema = BoothCreateSchema(**minimal_payload)
        owner_id = first_test_client_user.id

        # 2. Call the CRUD function
        created_booth = await create_booth(
            db=db_session,
            obj_in=booth_create_schema,
            owner_id=owner_id
        )

        # 3. Verify attributes
        assert created_booth.id is not None
        assert created_booth.owner_id == owner_id
        assert created_booth.title == minimal_payload["title"]

        # Assert optional fields are correctly set to None
        assert created_booth.description is None
        assert created_booth.tags is None
        assert created_booth.status == BoothStatus.PENDING
        assert created_booth.is_published is False

    async def test_create_booth_with_nonexistent_owner_return_error(
            self, db_session: AsyncSession,
            first_test_booth_payload: dict[str, str]
    ) -> None:
        """Test that creating a Booth with a non-existent owner ID fails.

        This test verifies that the CRUD function correctly raises an
        IntegrityError when attempting to create a Booth with an owner ID
        that doesn't exist in the users table, due to the foreign key
        constraint.
        """
        booth_create_schema = BoothCreateSchema(**first_test_booth_payload)

        # A random UUID that doesn't exist in the users table
        non_existent_owner_id = uuid4()

        # Expect a database-level IntegrityError because
        # the FK constraint will fail
        with pytest.raises(IntegrityError):
            await create_booth(
                db=db_session,
                obj_in=booth_create_schema,
                owner_id=non_existent_owner_id
            )

    async def test_create_booth_with_title_too_long_return_error(
            self, db_session: AsyncSession,
            first_test_client_user: "UserModel",
            first_test_booth_payload: dict[str, str]
    ) -> None:
        """Test that creating a Booth with a title that's too long fails.

        This test verifies that the CRUD function correctly raises a
        ValidationError when attempting to create a Booth with a title that
        exceeds the maximum length of 120 characters.

        The test covers the following checks:

        1. The test creates a BoothCreateSchema instance with a title that's
           one character longer than the maximum allowed length.
        2. The test calls the create_booth CRUD function with the
           BoothCreateSchema instance and the ID of a valid User.
        3. The test verifies that a ValidationError is raised.
        4. The test checks that the error message is as expected.
        """
        long_title = "a" * 121  # One character over the limit of 120
        first_test_booth_payload["title"] = long_title

        # Pydantic should raise a ValidationError before
        # the database is even hit.
        # type character varying(120)"
        with pytest.raises(ValidationError) as exc_info:
            booth_create_schema = BoothCreateSchema(
                **first_test_booth_payload
            )
            owner_id = first_test_client_user.id

            await create_booth(
                db=db_session,
                obj_in=booth_create_schema,
                owner_id=owner_id
            )

        # Check that the error message is as expected
        assert len(exc_info.value.errors()) == 1
        assert exc_info.value.errors()[0]['type'] == 'string_too_long'
