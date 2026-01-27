"""Unit tests for Lender model."""

from datetime import datetime

import pytest

from app.models import Lender


class TestLenderCreation:
    """Tests for creating Lender instances."""

    def test_lender_creation_with_required_fields(self):
        """Test creating a lender with required fields."""
        lender = Lender(
            id="citizens_bank",
            name="Citizens Bank",
            policy_file="citizens_bank.yaml",
        )
        assert lender.id == "citizens_bank"
        assert lender.name == "Citizens Bank"
        assert lender.policy_file == "citizens_bank.yaml"
        assert lender.is_active is True
        assert lender.policy_version == 1

    def test_lender_creation_with_all_fields(self):
        """Test creating a lender with all fields."""
        lender = Lender(
            id="apex_commercial",
            name="Apex Commercial Capital",
            logo_url="https://example.com/apex-logo.png",
            contact_name="John Smith",
            contact_email="john@apex.com",
            contact_phone="555-123-4567",
            is_active=True,
            policy_file="apex_commercial.yaml",
            policy_version=2,
        )
        assert lender.logo_url == "https://example.com/apex-logo.png"
        assert lender.contact_name == "John Smith"
        assert lender.policy_version == 2


class TestPolicyFileReference:
    """Tests for policy file reference."""

    def test_policy_file_path(self):
        """Test policy file path."""
        lender = Lender(
            id="stearns_bank",
            name="Stearns Bank",
            policy_file="lenders/stearns_bank.yaml",
        )
        assert lender.policy_file == "lenders/stearns_bank.yaml"


class TestActiveStatusToggle:
    """Tests for toggling lender active status."""

    def test_toggle_status_to_inactive(self):
        """Test toggling from active to inactive."""
        lender = Lender(
            id="test_lender",
            name="Test Lender",
            policy_file="test.yaml",
            is_active=True,
        )
        lender.toggle_status()
        assert lender.is_active is False

    def test_toggle_status_to_active(self):
        """Test toggling from inactive to active."""
        lender = Lender(
            id="test_lender",
            name="Test Lender",
            policy_file="test.yaml",
            is_active=False,
        )
        lender.toggle_status()
        assert lender.is_active is True


class TestPolicyVersionUpdate:
    """Tests for updating policy version."""

    def test_update_policy_version(self):
        """Test incrementing policy version."""
        lender = Lender(
            id="test_lender",
            name="Test Lender",
            policy_file="test.yaml",
            policy_version=1,
        )
        original_time = lender.policy_last_updated
        lender.update_policy_version()
        assert lender.policy_version == 2
        # Note: In a real test with database, we'd verify timestamp changed

    def test_update_policy_version_multiple_times(self):
        """Test incrementing policy version multiple times."""
        lender = Lender(
            id="test_lender",
            name="Test Lender",
            policy_file="test.yaml",
            policy_version=1,
        )
        lender.update_policy_version()
        lender.update_policy_version()
        lender.update_policy_version()
        assert lender.policy_version == 4


class TestLenderRepr:
    """Tests for Lender __repr__."""

    def test_repr_format(self):
        """Test that __repr__ returns expected format."""
        lender = Lender(
            id="citizens_bank",
            name="Citizens Bank",
            policy_file="citizens_bank.yaml",
            is_active=True,
        )
        repr_str = repr(lender)
        assert "Lender" in repr_str
        assert "citizens_bank" in repr_str
        assert "Citizens Bank" in repr_str
        assert "active=True" in repr_str
