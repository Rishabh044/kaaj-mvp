"""Tests for the configuration module."""

import os
from unittest.mock import patch

import pytest

from app.core.config import Settings


class TestConfig:
    """Tests for the Settings class."""

    def test_config_loads_from_env(self):
        """Verify config loads from environment variables."""
        env_vars = {
            "DATABASE_HOST": "test-host",
            "DATABASE_PORT": "5433",
            "DATABASE_USER": "test-user",
            "DATABASE_PASSWORD": "test-password",
            "DATABASE_NAME": "test-db",
            "APP_ENV": "production",
            "DEBUG": "false",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings.database_host == "test-host"
            assert settings.database_port == 5433
            assert settings.database_user == "test-user"
            assert settings.database_password == "test-password"
            assert settings.database_name == "test-db"
            assert settings.app_env == "production"
            assert settings.debug is False

    def test_config_defaults(self):
        """Verify sensible defaults are set."""
        # Clear relevant env vars to test defaults
        env_vars_to_clear = [
            "DATABASE_HOST",
            "DATABASE_PORT",
            "DATABASE_USER",
            "DATABASE_PASSWORD",
            "DATABASE_NAME",
            "APP_ENV",
            "DEBUG",
        ]
        env_backup = {k: os.environ.pop(k, None) for k in env_vars_to_clear}

        try:
            settings = Settings()
            assert settings.database_host == "localhost"
            assert settings.database_port == 5432
            assert settings.database_user == "postgres"
            assert settings.database_password == "postgres"
            assert settings.database_name == "lender_matching"
            assert settings.app_env == "development"
            assert settings.debug is True
        finally:
            # Restore env vars
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v

    def test_database_url_construction(self):
        """Verify DATABASE_URL is correctly constructed."""
        env_vars = {
            "DATABASE_HOST": "db.example.com",
            "DATABASE_PORT": "5432",
            "DATABASE_USER": "myuser",
            "DATABASE_PASSWORD": "mypassword",
            "DATABASE_NAME": "mydb",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            expected_url = (
                "postgresql+asyncpg://myuser:mypassword@db.example.com:5432/mydb"
            )
            assert settings.database_url == expected_url

    def test_database_url_sync_construction(self):
        """Verify sync DATABASE_URL is correctly constructed."""
        env_vars = {
            "DATABASE_HOST": "db.example.com",
            "DATABASE_PORT": "5432",
            "DATABASE_USER": "myuser",
            "DATABASE_PASSWORD": "mypassword",
            "DATABASE_NAME": "mydb",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            expected_url = "postgresql://myuser:mypassword@db.example.com:5432/mydb"
            assert settings.database_url_sync == expected_url

    def test_is_development(self):
        """Test is_development property."""
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
            settings = Settings()
            assert settings.is_development is True
            assert settings.is_production is False

    def test_is_production(self):
        """Test is_production property."""
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False
