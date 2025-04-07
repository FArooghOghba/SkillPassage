"""
Database configuration settings using Pydantic BaseSettings.

This module contains settings for database connection configuration,
loaded from environment variables.
"""
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class DatabaseSettings(BaseSettings):
    """
    Database configuration settings.

    Attributes:
        DATABASE_URL: SQLAlchemy connection string for the database
    """

    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Default instance using .env
db_settings = DatabaseSettings()
