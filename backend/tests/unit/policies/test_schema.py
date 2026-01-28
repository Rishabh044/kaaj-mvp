"""Unit tests for policy schema validation."""

import pytest
from pydantic import ValidationError

from app.policies.schema import (
    CreditScoreCriteria,
    BusinessCriteria,
    CreditHistoryCriteria,
    EquipmentCriteria,
    GeographicCriteria,
    IndustryCriteria,
    TransactionCriteria,
    LoanAmountCriteria,
    ProgramCriteria,
    LenderProgram,
    EquipmentTermMatrix,
    EquipmentTermEntry,
    LenderPolicy,
    LenderRestrictions,
    ScoringConfig,
)


class TestCreditScoreCriteria:
    """Tests for CreditScoreCriteria validation."""

    def test_valid_fico_score(self):
        """Test valid FICO score criteria."""
        criteria = CreditScoreCriteria(type="fico", min=700)
        assert criteria.type == "fico"
        assert criteria.min == 700

    def test_valid_transunion_score(self):
        """Test valid TransUnion score criteria."""
        criteria = CreditScoreCriteria(type="transunion", min=680)
        assert criteria.type == "transunion"
        assert criteria.min == 680

    def test_valid_paynet_score(self):
        """Test valid PayNet score criteria."""
        criteria = CreditScoreCriteria(type="paynet", min=310)
        assert criteria.type == "paynet"
        assert criteria.min == 310

    def test_invalid_score_type(self):
        """Test invalid score type raises error."""
        with pytest.raises(ValidationError) as exc_info:
            CreditScoreCriteria(type="invalid", min=700)
        assert "type" in str(exc_info.value)

    def test_score_below_minimum(self):
        """Test score below 300 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            CreditScoreCriteria(type="fico", min=200)
        assert "min" in str(exc_info.value)

    def test_score_above_maximum(self):
        """Test score above 850 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            CreditScoreCriteria(type="fico", min=900)
        assert "min" in str(exc_info.value)

    def test_default_type_is_fico(self):
        """Test default score type is FICO."""
        criteria = CreditScoreCriteria(min=700)
        assert criteria.type == "fico"


class TestBusinessCriteria:
    """Tests for BusinessCriteria validation."""

    def test_valid_business_criteria(self):
        """Test valid business criteria."""
        criteria = BusinessCriteria(
            min_time_in_business_years=2.5,
            requires_homeowner=True,
            requires_cdl="conditional",
            min_cdl_years=5,
            min_industry_experience_years=3,
            min_fleet_size=5,
            requires_us_citizen=True,
        )
        assert criteria.min_time_in_business_years == 2.5
        assert criteria.requires_homeowner is True
        assert criteria.requires_cdl == "conditional"
        assert criteria.min_cdl_years == 5

    def test_cdl_conditional_value(self):
        """Test CDL can be conditional."""
        criteria = BusinessCriteria(requires_cdl="conditional")
        assert criteria.requires_cdl == "conditional"

    def test_cdl_boolean_value(self):
        """Test CDL can be boolean."""
        criteria_true = BusinessCriteria(requires_cdl=True)
        criteria_false = BusinessCriteria(requires_cdl=False)
        assert criteria_true.requires_cdl is True
        assert criteria_false.requires_cdl is False

    def test_negative_tib_raises_error(self):
        """Test negative time in business raises error."""
        with pytest.raises(ValidationError):
            BusinessCriteria(min_time_in_business_years=-1)

    def test_all_optional_fields(self):
        """Test all fields are optional."""
        criteria = BusinessCriteria()
        assert criteria.min_time_in_business_years is None
        assert criteria.requires_homeowner is None
        assert criteria.requires_cdl is None


class TestCreditHistoryCriteria:
    """Tests for CreditHistoryCriteria validation."""

    def test_valid_credit_history(self):
        """Test valid credit history criteria."""
        criteria = CreditHistoryCriteria(
            max_bankruptcies=1,
            bankruptcy_min_discharge_years=5,
            allows_active_bankruptcy=False,
            max_open_judgements=0,
            allows_foreclosure=False,
            allows_repossession=True,
            max_tax_liens=0,
        )
        assert criteria.max_bankruptcies == 1
        assert criteria.bankruptcy_min_discharge_years == 5
        assert criteria.allows_active_bankruptcy is False

    def test_strict_no_derogatories(self):
        """Test strict no derogatory items config."""
        criteria = CreditHistoryCriteria(
            max_bankruptcies=0,
            max_open_judgements=0,
            allows_foreclosure=False,
            allows_repossession=False,
            max_tax_liens=0,
        )
        assert criteria.max_bankruptcies == 0
        assert criteria.max_open_judgements == 0

    def test_default_allows_active_bankruptcy_false(self):
        """Test default for active bankruptcy is False."""
        criteria = CreditHistoryCriteria()
        assert criteria.allows_active_bankruptcy is False


class TestGeographicCriteria:
    """Tests for GeographicCriteria validation."""

    def test_excluded_states(self):
        """Test excluded states list."""
        criteria = GeographicCriteria(excluded_states=["CA", "NY", "TX"])
        assert criteria.excluded_states == ["CA", "NY", "TX"]

    def test_allowed_states(self):
        """Test allowed states list."""
        criteria = GeographicCriteria(allowed_states=["TX", "OK", "LA"])
        assert criteria.allowed_states == ["TX", "OK", "LA"]

    def test_state_normalization_to_uppercase(self):
        """Test states are normalized to uppercase."""
        criteria = GeographicCriteria(excluded_states=["ca", "ny"])
        assert criteria.excluded_states == ["CA", "NY"]

    def test_mixed_case_normalization(self):
        """Test mixed case is normalized."""
        criteria = GeographicCriteria(allowed_states=["Tx", "oK"])
        assert criteria.allowed_states == ["TX", "OK"]


class TestLenderProgram:
    """Tests for LenderProgram validation."""

    def test_valid_program(self):
        """Test valid lender program."""
        program = LenderProgram(
            id="tier_1_general",
            name="Tier 1 - General Program",
            description="Best rates for established businesses",
            is_app_only=True,
            min_amount=1000000,
            max_amount=7500000,
            max_term_months=60,
        )
        assert program.id == "tier_1_general"
        assert program.name == "Tier 1 - General Program"
        assert program.is_app_only is True

    def test_program_id_normalized_to_lowercase(self):
        """Test program ID is normalized to lowercase."""
        program = LenderProgram(
            id="TIER_1_GENERAL",
            name="Test Program",
        )
        assert program.id == "tier_1_general"

    def test_program_id_allows_hyphens(self):
        """Test program ID allows hyphens."""
        program = LenderProgram(
            id="tier-1-general",
            name="Test Program",
        )
        assert program.id == "tier-1-general"

    def test_invalid_program_id_special_chars(self):
        """Test program ID rejects special characters."""
        with pytest.raises(ValidationError):
            LenderProgram(id="tier@1", name="Test")

    def test_default_is_app_only_false(self):
        """Test default is_app_only is False."""
        program = LenderProgram(id="test", name="Test")
        assert program.is_app_only is False

    def test_program_with_criteria(self):
        """Test program with full criteria."""
        program = LenderProgram(
            id="test_program",
            name="Test Program",
            criteria=ProgramCriteria(
                credit_score=CreditScoreCriteria(type="fico", min=700),
                business=BusinessCriteria(min_time_in_business_years=2),
            ),
        )
        assert program.criteria.credit_score.min == 700
        assert program.criteria.business.min_time_in_business_years == 2


class TestEquipmentTermMatrix:
    """Tests for EquipmentTermMatrix validation."""

    def test_valid_term_matrix(self):
        """Test valid equipment term matrix."""
        matrix = EquipmentTermMatrix(
            category="class_8_truck",
            entries=[
                EquipmentTermEntry(max_mileage=200000, term_months=60),
                EquipmentTermEntry(min_mileage=200001, max_mileage=400000, term_months=48),
            ],
        )
        assert matrix.category == "class_8_truck"
        assert len(matrix.entries) == 2
        assert matrix.entries[0].term_months == 60

    def test_term_entry_with_year_range(self):
        """Test term entry with year range."""
        entry = EquipmentTermEntry(min_year=2020, max_year=2024, term_months=60)
        assert entry.min_year == 2020
        assert entry.max_year == 2024


class TestLenderPolicy:
    """Tests for LenderPolicy validation."""

    def test_valid_lender_policy(self):
        """Test valid complete lender policy."""
        policy = LenderPolicy(
            id="test_lender",
            name="Test Lender",
            version=1,
            description="Test description",
            programs=[
                LenderProgram(id="program_1", name="Program 1"),
                LenderProgram(id="program_2", name="Program 2"),
            ],
        )
        assert policy.id == "test_lender"
        assert policy.name == "Test Lender"
        assert policy.version == 1
        assert len(policy.programs) == 2

    def test_lender_id_normalized_to_lowercase(self):
        """Test lender ID is normalized to lowercase."""
        policy = LenderPolicy(
            id="TEST_LENDER",
            name="Test Lender",
            version=1,
            programs=[LenderProgram(id="p1", name="P1")],
        )
        assert policy.id == "test_lender"

    def test_invalid_lender_id_special_chars(self):
        """Test lender ID rejects special characters."""
        with pytest.raises(ValidationError):
            LenderPolicy(
                id="test-lender",  # Hyphens not allowed for lender ID
                name="Test",
                version=1,
                programs=[LenderProgram(id="p1", name="P1")],
            )

    def test_duplicate_program_ids_raises_error(self):
        """Test duplicate program IDs raise error."""
        with pytest.raises(ValidationError) as exc_info:
            LenderPolicy(
                id="test_lender",
                name="Test Lender",
                version=1,
                programs=[
                    LenderProgram(id="program_1", name="Program 1"),
                    LenderProgram(id="program_1", name="Program 1 Duplicate"),
                ],
            )
        assert "unique" in str(exc_info.value).lower()

    def test_version_must_be_positive(self):
        """Test version must be at least 1."""
        with pytest.raises(ValidationError):
            LenderPolicy(
                id="test_lender",
                name="Test",
                version=0,
                programs=[LenderProgram(id="p1", name="P1")],
            )

    def test_policy_with_restrictions(self):
        """Test policy with global restrictions."""
        policy = LenderPolicy(
            id="test_lender",
            name="Test Lender",
            version=1,
            programs=[LenderProgram(id="p1", name="P1")],
            restrictions=LenderRestrictions(
                geographic=GeographicCriteria(excluded_states=["CA"]),
                industry=IndustryCriteria(excluded_industries=["cannabis"]),
            ),
        )
        assert policy.restrictions.geographic.excluded_states == ["CA"]
        assert "cannabis" in policy.restrictions.industry.excluded_industries

    def test_policy_with_scoring_config(self):
        """Test policy with custom scoring."""
        policy = LenderPolicy(
            id="test_lender",
            name="Test Lender",
            version=1,
            programs=[LenderProgram(id="p1", name="P1")],
            scoring=ScoringConfig(
                credit_score_weight=0.4,
                time_in_business_weight=0.3,
            ),
        )
        assert policy.scoring.credit_score_weight == 0.4
        assert policy.scoring.time_in_business_weight == 0.3


class TestScoringConfig:
    """Tests for ScoringConfig validation."""

    def test_valid_scoring_config(self):
        """Test valid scoring configuration."""
        config = ScoringConfig(
            credit_score_weight=0.3,
            time_in_business_weight=0.2,
            loan_amount_weight=0.2,
            equipment_fit_weight=0.15,
            credit_history_weight=0.15,
        )
        assert config.credit_score_weight == 0.3
        # Weights sum to 1.0
        total = (
            config.credit_score_weight
            + config.time_in_business_weight
            + config.loan_amount_weight
            + config.equipment_fit_weight
            + config.credit_history_weight
        )
        assert total == 1.0

    def test_weight_above_one_raises_error(self):
        """Test weight above 1.0 raises error."""
        with pytest.raises(ValidationError):
            ScoringConfig(credit_score_weight=1.5)

    def test_negative_weight_raises_error(self):
        """Test negative weight raises error."""
        with pytest.raises(ValidationError):
            ScoringConfig(credit_score_weight=-0.1)

    def test_default_weights(self):
        """Test default weight values."""
        config = ScoringConfig()
        assert config.credit_score_weight == 0.3
        assert config.time_in_business_weight == 0.2
        assert config.loan_amount_weight == 0.2
        assert config.equipment_fit_weight == 0.15
        assert config.credit_history_weight == 0.15
