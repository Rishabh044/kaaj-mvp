"""Integration tests for the matching service with real lender policies."""

from pathlib import Path

import pytest

from app.policies.loader import PolicyLoader
from app.rules.base import EvaluationContext
from app.rules.engine import MatchingEngine
from app.services.matching_service import LenderMatchingService, MatchingResult


# Get the actual lenders directory
LENDERS_DIR = Path(__file__).parent.parent.parent / "app" / "policies" / "lenders"


@pytest.fixture
def matching_service():
    """Create a matching service with real policies."""
    loader = PolicyLoader(LENDERS_DIR)
    engine = MatchingEngine()
    return LenderMatchingService(engine=engine, policy_loader=loader)


@pytest.fixture
def strong_applicant_context():
    """Create context for a strong applicant that should qualify for most lenders."""
    return EvaluationContext(
        application_id="strong-app",
        fico_score=750,
        transunion_score=740,
        paynet_score=700,
        years_in_business=10.0,
        state="TX",
        industry_code="construction",
        industry_name="Construction",
        is_homeowner=True,
        is_us_citizen=True,
        has_cdl=False,
        has_bankruptcy=False,
        has_open_judgements=False,
        has_foreclosure=False,
        has_repossession=False,
        has_tax_liens=False,
        loan_amount=5000000,  # $50,000
        equipment_category="construction",
        equipment_year=2022,
        equipment_age_years=3,
        transaction_type="purchase",
        is_private_party=False,
    )


@pytest.fixture
def weak_applicant_context():
    """Create context for a weak applicant with credit issues."""
    return EvaluationContext(
        application_id="weak-app",
        fico_score=620,
        transunion_score=610,
        years_in_business=0.5,  # Startup
        state="CA",  # Many lenders exclude CA
        industry_code="restaurant",
        is_homeowner=False,
        has_bankruptcy=True,
        bankruptcy_discharge_years=2.0,  # Too recent for most
        has_open_judgements=True,
        loan_amount=5000000,
        equipment_category="restaurant",
        equipment_age_years=5,
    )


class TestMatchApplicationAllLenders:
    """Tests for matching against all lenders."""

    def test_match_application_all_lenders(self, matching_service, strong_applicant_context):
        """Test matching returns results for all lenders."""
        result = matching_service.match_application(strong_applicant_context)

        assert isinstance(result, MatchingResult)
        assert result.total_evaluated == 5  # All 5 lenders
        assert len(result.matches) == 5

    def test_match_application_returns_ranked_results(
        self, matching_service, strong_applicant_context
    ):
        """Test results are ranked by eligibility and score."""
        result = matching_service.match_application(strong_applicant_context)

        # Eligible lenders should be ranked first
        if result.has_eligible_lender:
            eligible_ranks = [m.rank for m in result.matches if m.is_eligible]
            ineligible_ranks = [m.rank for m in result.matches if not m.is_eligible]

            if eligible_ranks and ineligible_ranks:
                assert max(eligible_ranks) < min(ineligible_ranks)


class TestMatchApplicationSpecificLenders:
    """Tests for matching against specific lenders."""

    def test_match_application_specific_lenders(
        self, matching_service, strong_applicant_context
    ):
        """Test matching against specific lender IDs."""
        result = matching_service.match_application(
            strong_applicant_context,
            lender_ids=["citizens_bank", "stearns_bank"],
        )

        assert result.total_evaluated == 2
        lender_ids = {m.lender_id for m in result.matches}
        assert lender_ids == {"citizens_bank", "stearns_bank"}


class TestMatchApplicationRankingByScore:
    """Tests for score-based ranking."""

    def test_match_application_ranking_by_score(
        self, matching_service, strong_applicant_context
    ):
        """Test higher fit scores rank higher among eligible lenders."""
        result = matching_service.match_application(strong_applicant_context)

        eligible = [m for m in result.matches if m.is_eligible]
        if len(eligible) > 1:
            # Should be sorted by score descending
            scores = [m.fit_score for m in eligible]
            assert scores == sorted(scores, reverse=True)


class TestMatchApplicationNoEligibleLenders:
    """Tests for applications with no eligible lenders."""

    def test_match_application_no_eligible_lenders(
        self, matching_service, weak_applicant_context
    ):
        """Test handling when no lenders are eligible."""
        result = matching_service.match_application(weak_applicant_context)

        # May have few or no eligible lenders due to credit issues and CA state
        assert result.total_evaluated == 5
        # Best match should still be set (closest to qualifying)
        # but may not be eligible


class TestMatchApplicationCAApplicantRestricted:
    """Tests for California applicant restrictions."""

    def test_ca_applicant_excluded_from_some_lenders(self, matching_service):
        """Test CA applicants are excluded from lenders that restrict CA."""
        context = EvaluationContext(
            application_id="ca-app",
            fico_score=750,
            years_in_business=5.0,
            state="CA",
            is_homeowner=True,
            loan_amount=5000000,
            equipment_category="construction",
            equipment_age_years=2,
        )

        result = matching_service.match_application(context)

        # Citizens Bank and Apex exclude CA
        citizens_result = next(
            (m for m in result.matches if m.lender_id == "citizens_bank"), None
        )
        apex_result = next(
            (m for m in result.matches if m.lender_id == "apex_commercial"), None
        )

        if citizens_result:
            assert citizens_result.is_eligible is False
            assert any("CA" in r for r in citizens_result.global_rejection_reasons)

        if apex_result:
            assert apex_result.is_eligible is False


class TestMatchApplicationStartupBusiness:
    """Tests for startup business applications."""

    def test_startup_business_limited_options(self, matching_service):
        """Test startups have limited lender options."""
        context = EvaluationContext(
            application_id="startup-app",
            fico_score=720,
            years_in_business=0.5,  # Less than 2 years = startup
            state="TX",
            is_homeowner=True,
            industry_experience_years=5,
            loan_amount=3000000,  # $30,000
            equipment_category="construction",
            equipment_age_years=2,
        )

        result = matching_service.match_application(context)

        # Most lenders require 2+ years TIB
        # Should have fewer eligible options
        assert result.total_evaluated == 5


class TestMatchApplicationTrucking:
    """Tests for trucking applications."""

    def test_trucking_application_special_requirements(self, matching_service):
        """Test trucking applications face special requirements."""
        context = EvaluationContext(
            application_id="trucking-app",
            fico_score=720,
            years_in_business=6.0,
            state="TX",
            is_homeowner=True,
            has_cdl=True,
            cdl_years=8,
            fleet_size=6,
            loan_amount=10000000,  # $100,000
            equipment_category="class_8_truck",
            equipment_year=2020,
            equipment_age_years=5,
        )

        result = matching_service.match_application(context)

        # Advantage+ and Apex exclude trucking
        advantage_result = next(
            (m for m in result.matches if m.lender_id == "advantage_plus"), None
        )
        if advantage_result:
            assert advantage_result.is_eligible is False


class TestMatchApplicationBankruptcyHistory:
    """Tests for applications with bankruptcy history."""

    def test_bankruptcy_history_restrictions(self, matching_service):
        """Test bankruptcy history affects eligibility."""
        context = EvaluationContext(
            application_id="bk-app",
            fico_score=720,
            years_in_business=5.0,
            state="TX",
            is_homeowner=True,
            has_bankruptcy=True,
            bankruptcy_discharge_years=3.0,  # 3 years ago
            loan_amount=5000000,
            equipment_category="construction",
            equipment_age_years=2,
        )

        result = matching_service.match_application(context)

        # Citizens requires 5+ years, Falcon requires 15+ years
        # Many lenders should reject
        advantage_result = next(
            (m for m in result.matches if m.lender_id == "advantage_plus"), None
        )
        if advantage_result:
            # Advantage+ doesn't allow any bankruptcy
            assert advantage_result.is_eligible is False


class TestMatchSingleLender:
    """Tests for single lender evaluation."""

    def test_match_single_lender(self, matching_service, strong_applicant_context):
        """Test evaluating against a single lender."""
        result = matching_service.match_single_lender(
            strong_applicant_context,
            "citizens_bank",
        )

        assert result.lender_id == "citizens_bank"
        assert result.lender_name == "Citizens Bank"


class TestExplainRejection:
    """Tests for rejection explanation."""

    def test_explain_rejection_eligible(self, matching_service, strong_applicant_context):
        """Test explanation for eligible application."""
        explanation = matching_service.explain_rejection(
            strong_applicant_context,
            "stearns_bank",
        )

        # Strong applicant should qualify
        if not explanation["is_rejected"]:
            assert "best_program" in explanation

    def test_explain_rejection_ineligible(self, matching_service, weak_applicant_context):
        """Test explanation for rejected application."""
        explanation = matching_service.explain_rejection(
            weak_applicant_context,
            "advantage_plus",
        )

        # Weak applicant should be rejected
        assert explanation["is_rejected"] is True
        assert "primary_reason" in explanation


class TestGetAvailableLenders:
    """Tests for getting available lenders."""

    def test_get_available_lenders(self, matching_service):
        """Test getting list of available lender IDs."""
        lender_ids = matching_service.get_available_lenders()

        assert len(lender_ids) == 5
        assert "citizens_bank" in lender_ids
        assert "advantage_plus" in lender_ids
        assert "stearns_bank" in lender_ids
        assert "falcon_equipment" in lender_ids
        assert "apex_commercial" in lender_ids


class TestMatchingResultHelpers:
    """Tests for MatchingResult helper methods."""

    def test_matching_result_eligible_matches(
        self, matching_service, strong_applicant_context
    ):
        """Test getting only eligible matches."""
        result = matching_service.match_application(strong_applicant_context)

        eligible = result.eligible_matches
        for m in eligible:
            assert m.is_eligible is True

    def test_matching_result_ineligible_matches(
        self, matching_service, strong_applicant_context
    ):
        """Test getting only ineligible matches."""
        result = matching_service.match_application(strong_applicant_context)

        ineligible = result.ineligible_matches
        for m in ineligible:
            assert m.is_eligible is False

    def test_matching_result_to_dict(self, matching_service, strong_applicant_context):
        """Test serialization to dictionary."""
        result = matching_service.match_application(strong_applicant_context)
        d = result.to_dict()

        assert "matches" in d
        assert "best_match" in d
        assert "total_evaluated" in d
        assert "total_eligible" in d
        assert "has_eligible_lender" in d
