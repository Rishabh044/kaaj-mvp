"""Unit tests for BusinessCredit model."""

import uuid
from datetime import date

import pytest

from app.models import BusinessCredit


class TestBusinessCreditCreation:
    """Tests for creating BusinessCredit instances."""

    def test_business_credit_creation_with_required_fields(self):
        """Test creating business credit with only required fields."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
        )
        assert credit.paynet_score is None
        assert credit.paydex_score is None
        assert credit.has_slow_pays is False

    def test_business_credit_creation_with_paynet(self):
        """Test creating business credit with PayNet scores."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            paynet_score=85,
            paynet_master_score=82,
        )
        assert credit.paynet_score == 85
        assert credit.paynet_master_score == 82
        assert credit.has_paynet is True

    def test_business_credit_creation_with_dnb(self):
        """Test creating business credit with D&B data."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            duns_number="123456789",
            dnb_rating="2A2",
            paydex_score=75,
        )
        assert credit.duns_number == "123456789"
        assert credit.dnb_rating == "2A2"
        assert credit.paydex_score == 75
        assert credit.has_dnb is True


class TestPaynetScoreRange:
    """Tests for PayNet score handling."""

    def test_paynet_score_valid_range(self):
        """Test PayNet score in valid range."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            paynet_score=90,
        )
        assert credit.paynet_score == 90

    def test_paynet_score_minimum(self):
        """Test PayNet score at minimum."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            paynet_score=0,
        )
        assert credit.paynet_score == 0

    def test_paynet_score_maximum(self):
        """Test PayNet score at maximum (typically 100)."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            paynet_score=100,
        )
        assert credit.paynet_score == 100


class TestTradeLines:
    """Tests for trade line information."""

    def test_trade_lines_full_info(self):
        """Test creating business credit with trade line info."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            trade_line_count=5,
            highest_credit=50000,
            average_days_to_pay=25,
        )
        assert credit.trade_line_count == 5
        assert credit.highest_credit == 50000
        assert credit.average_days_to_pay == 25

    def test_slow_pays(self):
        """Test slow pay tracking."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            has_slow_pays=True,
            slow_pay_count=3,
        )
        assert credit.has_slow_pays is True
        assert credit.slow_pay_count == 3


class TestHasPaynetProperty:
    """Tests for has_paynet property."""

    def test_has_paynet_true(self):
        """Test has_paynet is True when score exists."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            paynet_score=80,
        )
        assert credit.has_paynet is True

    def test_has_paynet_false(self):
        """Test has_paynet is False when no score."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
        )
        assert credit.has_paynet is False


class TestHasDnbProperty:
    """Tests for has_dnb property."""

    def test_has_dnb_true_with_rating(self):
        """Test has_dnb is True when rating exists."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            dnb_rating="1R1",
        )
        assert credit.has_dnb is True

    def test_has_dnb_true_with_paydex(self):
        """Test has_dnb is True when paydex exists."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
            paydex_score=80,
        )
        assert credit.has_dnb is True

    def test_has_dnb_false(self):
        """Test has_dnb is False when no D&B data."""
        credit = BusinessCredit(
            business_id=uuid.uuid4(),
        )
        assert credit.has_dnb is False


class TestBusinessCreditRepr:
    """Tests for BusinessCredit __repr__."""

    def test_repr_format(self):
        """Test that __repr__ returns expected format."""
        business_id = uuid.uuid4()
        credit = BusinessCredit(
            business_id=business_id,
            paynet_score=85,
        )
        repr_str = repr(credit)
        assert "BusinessCredit" in repr_str
        assert "paynet=85" in repr_str
