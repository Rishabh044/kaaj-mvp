"""Unit tests for the matching engine."""

import pytest

from app.policies.schema import (
    LenderPolicy,
    LenderProgram,
    ProgramCriteria,
    CreditScoreCriteria,
    BusinessCriteria,
    CreditHistoryCriteria,
    GeographicCriteria,
    LenderRestrictions,
)
from app.rules.base import EvaluationContext
from app.rules.engine import MatchingEngine, LenderMatchResult, ProgramMatchResult


@pytest.fixture
def engine():
    """Create a matching engine instance."""
    return MatchingEngine()


@pytest.fixture
def basic_context():
    """Create a basic evaluation context."""
    return EvaluationContext(
        application_id="test-app",
        fico_score=720,
        transunion_score=710,
        years_in_business=5.0,
        state="TX",
        is_homeowner=True,
        has_bankruptcy=False,
        loan_amount=5000000,  # $50,000
        equipment_category="construction",
        equipment_age_years=3,
    )


@pytest.fixture
def simple_policy():
    """Create a simple lender policy."""
    return LenderPolicy(
        id="test_lender",
        name="Test Lender",
        version=1,
        programs=[
            LenderProgram(
                id="standard",
                name="Standard Program",
                min_amount=1000000,  # $10,000
                max_amount=10000000,  # $100,000
                criteria=ProgramCriteria(
                    credit_score=CreditScoreCriteria(type="fico", min=700),
                    business=BusinessCriteria(min_time_in_business_years=2),
                ),
            ),
        ],
    )


class TestEvaluateLenderEligible:
    """Tests for eligible lender evaluations."""

    def test_evaluate_lender_eligible(self, engine, basic_context, simple_policy):
        """Test evaluation returns eligible when all criteria pass."""
        result = engine.evaluate_lender(basic_context, simple_policy)

        assert result.is_eligible is True
        assert result.lender_id == "test_lender"
        assert result.best_program is not None
        assert result.best_program.is_eligible is True
        assert result.fit_score > 0

    def test_evaluate_lender_fit_score_calculation(
        self, engine, basic_context, simple_policy
    ):
        """Test fit score is calculated properly."""
        result = engine.evaluate_lender(basic_context, simple_policy)

        assert 0 <= result.fit_score <= 100
        assert result.best_program.fit_score > 0


class TestEvaluateLenderIneligibleCreditScore:
    """Tests for ineligible due to credit score."""

    def test_evaluate_lender_ineligible_credit_score(self, engine, simple_policy):
        """Test evaluation fails when credit score is too low."""
        context = EvaluationContext(
            application_id="test-app",
            fico_score=650,  # Below minimum of 700
            years_in_business=5.0,
            loan_amount=5000000,
        )

        result = engine.evaluate_lender(context, simple_policy)

        assert result.is_eligible is False
        assert len(result.best_program.rejection_reasons) > 0
        assert any(
            "credit" in r.lower() for r in result.best_program.rejection_reasons
        )


class TestEvaluateLenderIneligibleState:
    """Tests for ineligible due to state restriction."""

    def test_evaluate_lender_ineligible_state(self, engine, basic_context):
        """Test evaluation fails when state is excluded."""
        policy = LenderPolicy(
            id="test_lender",
            name="Test Lender",
            version=1,
            programs=[
                LenderProgram(
                    id="standard",
                    name="Standard Program",
                    criteria=ProgramCriteria(),
                ),
            ],
            restrictions=LenderRestrictions(
                geographic=GeographicCriteria(excluded_states=["TX"]),  # Context is TX
            ),
        )

        result = engine.evaluate_lender(basic_context, policy)

        assert result.is_eligible is False
        assert len(result.global_rejection_reasons) > 0
        assert any("TX" in r for r in result.global_rejection_reasons)


class TestEvaluateLenderMultipleProgramsBestMatch:
    """Tests for selecting best program from multiple options."""

    def test_evaluate_lender_multiple_programs_best_match(self, engine, basic_context):
        """Test best program is selected when multiple are eligible."""
        policy = LenderPolicy(
            id="test_lender",
            name="Test Lender",
            version=1,
            programs=[
                LenderProgram(
                    id="tier_1",
                    name="Tier 1 - Best Rates",
                    min_amount=5000000,  # $50,000
                    max_amount=10000000,
                    criteria=ProgramCriteria(
                        credit_score=CreditScoreCriteria(type="fico", min=750),
                    ),
                ),
                LenderProgram(
                    id="tier_2",
                    name="Tier 2 - Standard",
                    min_amount=1000000,
                    max_amount=7500000,
                    criteria=ProgramCriteria(
                        credit_score=CreditScoreCriteria(type="fico", min=700),
                    ),
                ),
            ],
        )

        result = engine.evaluate_lender(basic_context, policy)

        # Should be eligible for tier_2 (720 >= 700) but not tier_1 (720 < 750)
        assert result.is_eligible is True
        assert result.best_program.program_id == "tier_2"


class TestEvaluateLenderRejectionReasons:
    """Tests for rejection reason compilation."""

    def test_evaluate_lender_rejection_reasons(self, engine):
        """Test rejection reasons are properly collected."""
        context = EvaluationContext(
            application_id="test-app",
            fico_score=600,  # Too low
            years_in_business=0.5,  # Too short
            loan_amount=5000000,
        )

        policy = LenderPolicy(
            id="test_lender",
            name="Test Lender",
            version=1,
            programs=[
                LenderProgram(
                    id="standard",
                    name="Standard",
                    criteria=ProgramCriteria(
                        credit_score=CreditScoreCriteria(type="fico", min=700),
                        business=BusinessCriteria(min_time_in_business_years=2),
                    ),
                ),
            ],
        )

        result = engine.evaluate_lender(context, policy)

        assert result.is_eligible is False
        assert len(result.best_program.rejection_reasons) >= 2


class TestEvaluateLenderProgramAmountBounds:
    """Tests for program amount bounds checking."""

    def test_loan_amount_below_minimum(self, engine, simple_policy):
        """Test loan amount below program minimum fails."""
        context = EvaluationContext(
            application_id="test-app",
            fico_score=720,
            years_in_business=5.0,
            loan_amount=500000,  # $5,000 - below $10,000 minimum
        )

        result = engine.evaluate_lender(context, simple_policy)

        assert result.is_eligible is False
        assert any("minimum" in r.lower() for r in result.best_program.rejection_reasons)

    def test_loan_amount_above_maximum(self, engine, simple_policy):
        """Test loan amount above program maximum fails."""
        context = EvaluationContext(
            application_id="test-app",
            fico_score=720,
            years_in_business=5.0,
            loan_amount=15000000,  # $150,000 - above $100,000 maximum
        )

        result = engine.evaluate_lender(context, simple_policy)

        assert result.is_eligible is False
        assert any("maximum" in r.lower() for r in result.best_program.rejection_reasons)


class TestProgramMatchResult:
    """Tests for ProgramMatchResult dataclass."""

    def test_program_match_result_counts(self):
        """Test passed/failed criteria counts."""
        from app.rules.base import RuleResult

        result = ProgramMatchResult(
            program_id="test",
            program_name="Test",
            is_eligible=False,
            criteria_results=[
                RuleResult(
                    passed=True,
                    rule_name="Credit Score",
                    required_value="700",
                    actual_value="720",
                    message="Passes",
                    score=80,
                ),
                RuleResult(
                    passed=False,
                    rule_name="TIB",
                    required_value="2 years",
                    actual_value="1 year",
                    message="Fails",
                    score=0,
                ),
            ],
        )

        assert result.passed_criteria_count == 1
        assert result.failed_criteria_count == 1

    def test_program_match_result_to_dict(self):
        """Test serialization to dictionary."""
        result = ProgramMatchResult(
            program_id="test",
            program_name="Test Program",
            is_eligible=True,
            fit_score=85.0,
        )

        d = result.to_dict()

        assert d["program_id"] == "test"
        assert d["is_eligible"] is True
        assert d["fit_score"] == 85.0


class TestLenderMatchResult:
    """Tests for LenderMatchResult dataclass."""

    def test_lender_match_result_eligible_program_count(self):
        """Test eligible program count calculation."""
        result = LenderMatchResult(
            lender_id="test",
            lender_name="Test",
            is_eligible=True,
            program_results=[
                ProgramMatchResult(
                    program_id="p1", program_name="P1", is_eligible=True
                ),
                ProgramMatchResult(
                    program_id="p2", program_name="P2", is_eligible=False
                ),
                ProgramMatchResult(
                    program_id="p3", program_name="P3", is_eligible=True
                ),
            ],
        )

        assert result.eligible_program_count == 2

    def test_lender_match_result_primary_rejection_reason(self):
        """Test primary rejection reason extraction."""
        result = LenderMatchResult(
            lender_id="test",
            lender_name="Test",
            is_eligible=False,
            global_rejection_reasons=["State excluded", "Industry restricted"],
        )

        assert result.primary_rejection_reason == "State excluded"

    def test_lender_match_result_to_dict(self):
        """Test serialization to dictionary."""
        result = LenderMatchResult(
            lender_id="test_lender",
            lender_name="Test Lender",
            is_eligible=True,
            fit_score=90.0,
            rank=1,
        )

        d = result.to_dict()

        assert d["lender_id"] == "test_lender"
        assert d["is_eligible"] is True
        assert d["fit_score"] == 90.0
        assert d["rank"] == 1
