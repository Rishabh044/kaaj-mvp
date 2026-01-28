"""Hatchet workflow orchestration client setup."""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Hatchet client instance (lazy initialization)
_hatchet_client = None


def get_hatchet():
    """Get or create the Hatchet client instance.

    Returns:
        Hatchet client instance, or None if not configured.
    """
    global _hatchet_client

    if _hatchet_client is not None:
        return _hatchet_client

    if not settings.hatchet_client_token:
        logger.warning(
            "HATCHET_CLIENT_TOKEN not configured. Workflow orchestration disabled."
        )
        return None

    try:
        from hatchet_sdk import Hatchet

        _hatchet_client = Hatchet()
        logger.info("Hatchet client initialized successfully")
        return _hatchet_client
    except ImportError:
        logger.warning("hatchet_sdk not installed. Workflow orchestration disabled.")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Hatchet client: {e}")
        return None


def hatchet_available() -> bool:
    """Check if Hatchet workflow orchestration is available.

    Returns:
        True if Hatchet is configured and available.
    """
    return get_hatchet() is not None


class MockHatchetContext:
    """Mock Hatchet context for testing and development without Hatchet."""

    def __init__(self, input_data: Optional[dict] = None):
        self._input = input_data or {}
        self._step_outputs = {}

    def workflow_input(self) -> dict:
        """Get the workflow input data."""
        return self._input

    def step_output(self, step_name: str) -> dict:
        """Get output from a previous step."""
        return self._step_outputs.get(step_name, {})

    def set_step_output(self, step_name: str, output: dict):
        """Set output for a step (for testing)."""
        self._step_outputs[step_name] = output

    def log(self, message: str):
        """Log a message."""
        logger.info(f"[Workflow] {message}")
