"""Tests for the database module."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, async_session_factory, engine


class TestDatabase:
    """Tests for database configuration."""

    def test_engine_creation(self):
        """Verify async engine is created."""
        assert engine is not None
        assert str(engine.url).startswith("postgresql+asyncpg://")

    def test_session_factory(self):
        """Verify session factory produces valid sessions."""
        assert async_session_factory is not None
        # The factory should be configured correctly
        assert async_session_factory.class_ == AsyncSession

