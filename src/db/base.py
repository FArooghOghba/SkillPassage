"""
SQLAlchemy declarative base configuration.

This module provides the base class for SQLAlchemy models,
ensuring consistent model configuration across the application.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.

    All database models should inherit from this class to ensure
    consistent configuration and behavior.

    Example:
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
    """

    pass
