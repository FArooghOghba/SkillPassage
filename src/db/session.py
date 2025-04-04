"""
Database session management.

This module provides utilities for managing database sessions and connections,
including async session creation and dependency injection.
"""
from typing import (
    Annotated,
    AsyncGenerator,
)

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import db_settings


# Create async engine for database connection
engine = create_async_engine(
    db_settings.DATABASE_URL,
    echo=False,  # Set to True to log all SQL queries
    future=True,  # Use SQLAlchemy 2.0 style
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,  # Transactions are not automatically committed
    autoflush=False,  # Changes are not automatically flushed
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db)):
            # Use session for database operations
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Type annotation for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
