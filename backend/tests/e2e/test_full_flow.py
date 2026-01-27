"""End-to-end tests for the complete application flow."""

import pytest
from pathlib import Path

from app.rules.context_builder import build_evaluation_context
from app.services.matching_service import LenderMatchingService
from app.rules.engine import MatchingEngine
from app.policies.loader import PolicyLoader


LENDERS_DIR = Path(__file__).parent.parent.parent / "app" / "policies" / "lenders"


class TestFullFlow:
    """Tests for the complete application evaluation flow."""

    @pytest.fixture
    def matching_service(self):
        """Create a matching service with real policies."""
        policy_loader = PolicyLoader(LENDERS_DIR)
        engine = MatchingEngine()
        return LenderMatchingService(engine=engine, policy_loader=policy_loader)

    def test_standard_application_qualifies_for_multiple_lenders(
        self, matching_service
    ):
        """Test a standard qualified application matches multiple lenders."""
        context = build_evaluation_context(
            application_id="test-standard-001",
            guarantor={
                "fico_score": 720,
                "is_homeowner": True,
                "is_us_citizen": True,
            },
            business={
                "years_in_business": 5.0,
                "state": "TX",
            },
            loan_request={
                "loan_amount": 5000000,
                "transaction_type": "purchase",
            },
            equipment={
                "category": "construction",
                "year": 2022,
            },
        )

        result = matching_service.match_application(context)

        assert result.total_evaluated == 5
        assert result.total_eligible >= 2
        assert result.has_eligible_lender

    def test_ca_applicant_restricted_from_some_lenders(self, matching_service):
        """Test California applicant is restricted from certain lenders."""
        context = build_evaluation_context(
            application_id="test-ca-001",
            guarantor={
                "fico_score": 720,
                "is_homeowner": True,
                "is_us_citizen": True,
            },
            business={
                "years_in_business": 5.0,
                "state": "CA",
            },
            loan_request={
                "loan_amount": 5000000,
                "transaction_type": "purchase",
            },
            equipment={
                "category": "construction",
                "year": 2022,
            },
        )

        result = matching_service.match_application(context)

        # CA is restricted by some lenders
        ineligible_ids = [m.lender_id for m in result.matches if not m.is_eligible]

        # Check that at least one lender rejected due to state
        assert any(
            "state" in str(m.global_rejection_reasons).lower()
            for m in result.matches
            if not m.is_eligible
        )

    def test_startup_business_limited_options(self, matching_service):
        """Test startup business has limited lender options."""
        context = build_evaluation_context(
            application_id="test-startup-001",
            guarantor={
                "fico_score": 750,
                "is_homeowner": True,
                "is_us_citizen": True,
            },
            business={
                "years_in_business": 0.5,
                "state": "TX",
            },
            loan_request={
                "loan_amount": 5000000,
                "transaction_type": "purchase",
            },
            equipment={
                "category": "construction",
                "year": 2022,
            },
        )

        result = matching_service.match_application(context)

        # Startups have fewer options
        assert result.total_eligible < result.total_evaluated

    def test_high_mileage_truck_term_restriction(self, matching_service):
        """Test high mileage truck gets appropriate term limits."""
        context = build_evaluation_context(
            application_id="test-highmile-001",
            guarantor={
                "fico_score": 700,
                "is_homeowner": True,
                "is_us_citizen": True,
                "has_cdl": True,
                "cdl_years": 5,
            },
            business={
                "years_in_business": 3.0,
                "state": "TX",
                "fleet_size": 5,
            },
            loan_request={
                "loan_amount": 10000000,
                "transaction_type": "purchase",
            },
            equipment={
                "category": "class_8_truck",
                "year": 2019,
                "mileage": 700000,
            },
        )

        result = matching_service.match_application(context)

        # Should still match some trucking-friendly lenders
        assert result.total_eligible >= 1

    def test_recent_bankruptcy_limited_options(self, matching_service):
        """Test recent bankruptcy severely limits options."""
        context = build_evaluation_context(
            application_id="test-bk-001",
            guarantor={
                "fico_score": 650,
                "is_homeowner": False,
                "is_us_citizen": True,
                "has_bankruptcy": True,
                "bankruptcy_discharge_years": 2,
            },
            business={
                "years_in_business": 5.0,
                "state": "TX",
            },
            loan_request={
                "loan_amount": 5000000,
                "transaction_type": "purchase",
            },
            equipment={
                "category": "construction",
                "year": 2022,
            },
        )

        result = matching_service.match_application(context)

        # Recent bankruptcy restricts many lenders
        assert result.total_eligible <= 2

    def test_no_paynet_uses_fico_fallback(self, matching_service):
        """Test application without PayNet score uses FICO fallback."""
        context = build_evaluation_context(
            application_id="test-nopaynet-001",
            guarantor={
                "fico_score": 720,
                "is_homeowner": True,
                "is_us_citizen": True,
            },
            business={
                "years_in_business": 5.0,
                "state": "TX",
            },
            loan_request={
                "loan_amount": 5000000,
                "transaction_type": "purchase",
            },
            equipment={
                "category": "construction",
                "year": 2022,
            },
            # No business_credit provided
        )

        result = matching_service.match_application(context)

        # Should still work without PayNet
        assert result.total_evaluated == 5

    def test_trucking_requires_cdl_and_fleet(self, matching_service):
        """Test trucking applications need CDL and fleet size for some lenders."""
        # Without CDL
        context_no_cdl = build_evaluation_context(
            application_id="test-truck-nocdl-001",
            guarantor={
                "fico_score": 700,
                "is_homeowner": True,
                "is_us_citizen": True,
                "has_cdl": False,
            },
            business={
                "years_in_business": 3.0,
                "state": "TX",
            },
            loan_request={
                "loan_amount": 10000000,
                "transaction_type": "purchase",
            },
            equipment={
                "category": "class_8_truck",
                "year": 2022,
            },
        )

        result_no_cdl = matching_service.match_application(context_no_cdl)

        # With CDL and fleet
        context_with_cdl = build_evaluation_context(
            application_id="test-truck-cdl-001",
            guarantor={
                "fico_score": 700,
                "is_homeowner": True,
                "is_us_citizen": True,
                "has_cdl": True,
                "cdl_years": 5,
            },
            business={
                "years_in_business": 3.0,
                "state": "TX",
                "fleet_size": 10,
            },
            loan_request={
                "loan_amount": 10000000,
                "transaction_type": "purchase",
            },
            equipment={
                "category": "class_8_truck",
                "year": 2022,
            },
        )

        result_with_cdl = matching_service.match_application(context_with_cdl)

        # Should qualify for more lenders with CDL and fleet
        assert result_with_cdl.total_eligible >= result_no_cdl.total_eligible

    def test_results_ranked_by_fit_score(self, matching_service):
        """Test that eligible lenders are ranked by fit score."""
        context = build_evaluation_context(
            application_id="test-ranking-001",
            guarantor={
                "fico_score": 720,
                "is_homeowner": True,
                "is_us_citizen": True,
            },
            business={
                "years_in_business": 5.0,
                "state": "TX",
            },
            loan_request={
                "loan_amount": 5000000,
                "transaction_type": "purchase",
            },
            equipment={
                "category": "construction",
                "year": 2022,
            },
        )

        result = matching_service.match_application(context)

        # Get eligible matches with ranks
        ranked = [m for m in result.matches if m.is_eligible and m.rank is not None]

        if len(ranked) > 1:
            # Ranks should be sequential
            ranks = sorted([m.rank for m in ranked])
            assert ranks == list(range(1, len(ranks) + 1))

            # Higher rank should have higher or equal score
            for i in range(len(ranked) - 1):
                m1 = next(m for m in ranked if m.rank == i + 1)
                m2 = next(m for m in ranked if m.rank == i + 2)
                assert m1.fit_score >= m2.fit_score
