"""Fixtures for booth-related tests."""
from typing import Dict

import pytest

from tests.factories.booth_factories import BoothFactory


@pytest.fixture
async def first_test_booth_payload() -> Dict[str, str]:
    """Fixture for creating a test Booth payload.

    This fixture uses the `BoothFactory` factory to create
    a test Booth payload. The created payload can be used
    in tests to simulate a Booth with predefined attributes
    for testing various scenarios.

    :return: a dict test Booth payload
    """
    return BoothFactory.create_payload()


# @pytest_asyncio.fixture
# async def first_test_booth(
#         db_session: AsyncSession, first_test_client_user: "User"
# ) -> "Booth":
#     """Fixture for creating a test Booth instance.
#
#     This fixture uses the `BoothFactory` factory to create
#     a test Booth instance. The created booth can be used
#     in tests to simulate a Booth with predefined attributes
#     for testing various scenarios.
#
#     :param db_session: The SQLAlchemy async session.
#     :param first_test_client_user: a valid User instance.
#     :return: a test Booth instance
#     """
#     booth = await BoothFactory.create_async(owner=first_test_client_user)
#     await db_session.commit()
#     await db_session.refresh(booth)
#     return booth
