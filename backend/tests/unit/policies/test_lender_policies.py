"""Unit tests for individual lender policy files."""

from pathlib import Path

import pytest

from app.policies.loader import PolicyLoader


# Get the actual lenders directory
LENDERS_DIR = Path(__file__).parent.parent.parent.parent / "app" / "policies" / "lenders"


@pytest.fixture
def policy_loader():
    """Create a policy loader pointing to actual lender files."""
    return PolicyLoader(LENDERS_DIR)


class TestCitizensBankPolicy:
    """Tests for Citizens Bank policy."""

    def test_citizens_bank_loads_successfully(self, policy_loader):
        """Test Citizens Bank policy loads without errors."""
        policy = policy_loader.load_policy("citizens_bank")
        assert policy.id == "citizens_bank"
        assert policy.name == "Citizens Bank"

    def test_citizens_bank_has_four_programs(self, policy_loader):
        """Test Citizens Bank has all expected programs."""
        policy = policy_loader.load_policy("citizens_bank")
        assert len(policy.programs) == 4

        program_ids = {p.id for p in policy.programs}
        assert "tier_1_general" in program_ids
        assert "tier_2_startup" in program_ids
        assert "tier_2_non_homeowner" in program_ids
        assert "tier_3_full_doc" in program_ids

    def test_citizens_bank_tier1_criteria(self, policy_loader):
        """Test Tier 1 program has correct criteria."""
        policy = policy_loader.load_policy("citizens_bank")
        tier1 = next(p for p in policy.programs if p.id == "tier_1_general")

        assert tier1.is_app_only is True
        assert tier1.max_amount == 7500000  # $75,000
        assert tier1.criteria.credit_score.type == "transunion"
        assert tier1.criteria.credit_score.min == 700
        assert tier1.criteria.business.min_time_in_business_years == 2
        assert tier1.criteria.business.requires_homeowner is True

    def test_citizens_bank_state_restrictions(self, policy_loader):
        """Test Citizens Bank excludes California."""
        policy = policy_loader.load_policy("citizens_bank")
        assert "CA" in policy.restrictions.geographic.excluded_states

    def test_citizens_bank_equipment_matrix(self, policy_loader):
        """Test Citizens Bank has equipment term matrices."""
        policy = policy_loader.load_policy("citizens_bank")
        assert policy.equipment_matrices is not None
        assert len(policy.equipment_matrices) > 0

        categories = {m.category for m in policy.equipment_matrices}
        assert "class_8_truck" in categories


class TestAdvantagePlusPolicy:
    """Tests for Advantage+ Financing policy."""

    def test_advantage_plus_loads_successfully(self, policy_loader):
        """Test Advantage+ policy loads without errors."""
        policy = policy_loader.load_policy("advantage_plus")
        assert policy.id == "advantage_plus"
        assert policy.name == "Advantage+ Financing"

    def test_advantage_plus_non_trucking_only(self, policy_loader):
        """Test Advantage+ excludes trucking."""
        policy = policy_loader.load_policy("advantage_plus")

        excluded_industries = policy.restrictions.industry.excluded_industries
        assert "trucking" in excluded_industries

    def test_advantage_plus_credit_history_strict(self, policy_loader):
        """Test Advantage+ has strict credit history requirements."""
        policy = policy_loader.load_policy("advantage_plus")

        # Check established business program
        established = next(p for p in policy.programs if p.id == "established_business")
        credit_history = established.criteria.credit_history

        assert credit_history.max_bankruptcies == 0
        assert credit_history.max_open_judgements == 0
        assert credit_history.allows_foreclosure is False
        assert credit_history.allows_repossession is False
        assert credit_history.max_tax_liens == 0

    def test_advantage_plus_loan_limits(self, policy_loader):
        """Test Advantage+ loan amount limits."""
        policy = policy_loader.load_policy("advantage_plus")

        for program in policy.programs:
            assert program.min_amount == 1000000  # $10,000
            assert program.max_amount == 7500000  # $75,000


class TestStearnsBankPolicy:
    """Tests for Stearns Bank policy."""

    def test_stearns_bank_loads_successfully(self, policy_loader):
        """Test Stearns Bank policy loads without errors."""
        policy = policy_loader.load_policy("stearns_bank")
        assert policy.id == "stearns_bank"
        assert policy.name == "Stearns Bank"

    def test_stearns_bank_tiered_programs(self, policy_loader):
        """Test Stearns Bank has multiple program tiers."""
        policy = policy_loader.load_policy("stearns_bank")

        # Should have standard, no-paynet, and corp-only tiers
        program_ids = {p.id for p in policy.programs}

        assert "tier_1_standard" in program_ids
        assert "tier_2_standard" in program_ids
        assert "tier_3_standard" in program_ids
        assert "tier_1_no_paynet" in program_ids
        assert "tier_1_corp_only" in program_ids

    def test_stearns_bank_bankruptcy_requirement(self, policy_loader):
        """Test Stearns Bank requires no bankruptcy in 7 years."""
        policy = policy_loader.load_policy("stearns_bank")

        for program in policy.programs:
            if program.criteria.credit_history:
                assert program.criteria.credit_history.bankruptcy_min_discharge_years == 7

    def test_stearns_bank_excluded_industries(self, policy_loader):
        """Test Stearns Bank has extensive industry exclusions."""
        policy = policy_loader.load_policy("stearns_bank")

        excluded = policy.restrictions.industry.excluded_industries
        assert "gambling" in excluded
        assert "restaurant" in excluded
        assert "car_wash" in excluded


class TestFalconEquipmentPolicy:
    """Tests for Falcon Equipment Finance policy."""

    def test_falcon_loads_successfully(self, policy_loader):
        """Test Falcon policy loads without errors."""
        policy = policy_loader.load_policy("falcon_equipment")
        assert policy.id == "falcon_equipment"
        assert policy.name == "Falcon Equipment Finance"

    def test_falcon_trucking_requirements(self, policy_loader):
        """Test Falcon trucking programs have specific requirements."""
        policy = policy_loader.load_policy("falcon_equipment")

        trucking_a = next(p for p in policy.programs if p.id == "trucking_a_credit")

        assert trucking_a.criteria.credit_score.min == 700
        assert trucking_a.criteria.business.min_time_in_business_years == 5
        assert trucking_a.criteria.business.min_fleet_size == 5

    def test_falcon_fleet_size_requirement(self, policy_loader):
        """Test Falcon requires 5+ trucks for trucking programs."""
        policy = policy_loader.load_policy("falcon_equipment")

        trucking_programs = [p for p in policy.programs if "trucking" in p.id]
        for program in trucking_programs:
            assert program.criteria.business.min_fleet_size == 5

    def test_falcon_bankruptcy_15_years(self, policy_loader):
        """Test Falcon requires 15+ years since bankruptcy."""
        policy = policy_loader.load_policy("falcon_equipment")

        for program in policy.programs:
            if program.criteria.credit_history:
                assert program.criteria.credit_history.bankruptcy_min_discharge_years == 15


class TestApexCommercialPolicy:
    """Tests for Apex Commercial Capital policy."""

    def test_apex_loads_successfully(self, policy_loader):
        """Test Apex policy loads without errors."""
        policy = policy_loader.load_policy("apex_commercial")
        assert policy.id == "apex_commercial"
        assert policy.name == "Apex Commercial Capital"

    def test_apex_state_restrictions(self, policy_loader):
        """Test Apex excludes CA, NV, ND, VT."""
        policy = policy_loader.load_policy("apex_commercial")

        excluded = policy.restrictions.geographic.excluded_states
        assert "CA" in excluded
        assert "NV" in excluded
        assert "ND" in excluded
        assert "VT" in excluded

    def test_apex_no_private_party(self, policy_loader):
        """Test Apex does not allow private party sales."""
        policy = policy_loader.load_policy("apex_commercial")
        assert policy.restrictions.transaction.allows_private_party is False

    def test_apex_no_sale_leaseback(self, policy_loader):
        """Test Apex does not allow sale-leaseback."""
        policy = policy_loader.load_policy("apex_commercial")
        assert policy.restrictions.transaction.allows_sale_leaseback is False

    def test_apex_tiered_rates(self, policy_loader):
        """Test Apex has multiple rate tiers."""
        policy = policy_loader.load_policy("apex_commercial")

        program_ids = {p.id for p in policy.programs}
        assert "standard_a_rate" in program_ids
        assert "standard_b_rate" in program_ids
        assert "standard_c_rate" in program_ids
        assert "a_plus_rate" in program_ids

    def test_apex_medical_program(self, policy_loader):
        """Test Apex has medical programs."""
        policy = policy_loader.load_policy("apex_commercial")

        medical_programs = [p for p in policy.programs if "medical" in p.id]
        assert len(medical_programs) >= 2

        medical_a = next(p for p in policy.programs if p.id == "medical_a_rate")
        assert "medical" in medical_a.criteria.industry.allowed_industries


class TestAllLendersLoadSuccessfully:
    """Meta-tests for all lender policies."""

    def test_all_lenders_load(self, policy_loader):
        """Test all lender policies load successfully."""
        lender_ids = policy_loader.get_all_lender_ids()

        # Should have 5 lenders
        assert len(lender_ids) == 5

        # All should load without errors
        for lender_id in lender_ids:
            policy = policy_loader.load_policy(lender_id)
            assert policy.id == lender_id
            assert policy.version >= 1
            assert len(policy.programs) > 0

    def test_all_lenders_have_valid_programs(self, policy_loader):
        """Test all lender programs have required fields."""
        policies = policy_loader.load_all_policies()

        for policy in policies:
            for program in policy.programs:
                assert program.id
                assert program.name
                # All programs should have max term
                assert program.max_term_months is None or program.max_term_months > 0
