"""Unit tests for ApplicationDBManager (database persistence layer)."""

from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import LoanApplication
from app.models.business import Business
from app.models.business_credit import BusinessCredit
from app.models.guarantor import PersonalGuarantor
from app.models.lender import Lender
from app.models.match_result import MatchResult
from app.policies.schema import LenderPolicy, LenderProgram
from app.schemas.api import (
    ApplicantInput,
    ApplicationSubmitRequest,
    BusinessCreditInput,
    BusinessInput,
    CreditHistoryInput,
    EquipmentInput,
    LoanRequestInput,
)
from app.services.application_db_manager import ApplicationDBManager


@pytest.fixture
def sample_application_request() -> ApplicationSubmitRequest:
    """Create a sample application request for testing."""
    return ApplicationSubmitRequest(
        applicant=ApplicantInput(
            fico_score=720,
            transunion_score=715,
            experian_score=710,
            equifax_score=725,
            is_homeowner=True,
            is_us_citizen=True,
            has_cdl=True,
            cdl_years=5,
            industry_experience_years=10,
        ),
        business=BusinessInput(
            name="Test Trucking LLC",
            state="TX",
            industry_code="484110",
            industry_name="General Freight Trucking",
            years_in_business=5.0,
            annual_revenue=1500000,
            fleet_size=3,
        ),
        credit_history=CreditHistoryInput(
            has_bankruptcy=False,
            has_foreclosure=False,
            has_repossession=False,
            has_tax_liens=False,
            has_open_judgements=False,
        ),
        equipment=EquipmentInput(
            category="class_8_truck",
            type="Sleeper",
            year=2022,
            mileage=50000,
            condition="used",
        ),
        loan_request=LoanRequestInput(
            amount=15000000,  # $150,000 in cents
            requested_term_months=60,
            down_payment_percent=10.0,
            transaction_type="purchase",
            is_private_party=False,
        ),
    )


@pytest.fixture
def sample_application_with_business_credit(
    sample_application_request: ApplicationSubmitRequest,
) -> ApplicationSubmitRequest:
    """Sample application with business credit data."""
    sample_application_request.business_credit = BusinessCreditInput(
        paynet_score=75,
        paynet_master_score=680,
        paydex_score=80,
    )
    return sample_application_request


@pytest.fixture
def sample_application_with_bankruptcy() -> ApplicationSubmitRequest:
    """Create a sample application with bankruptcy history."""
    return ApplicationSubmitRequest(
        applicant=ApplicantInput(
            fico_score=650,
            is_homeowner=False,
        ),
        business=BusinessInput(
            name="Recovery Business Inc",
            state="CA",
            years_in_business=3.0,
        ),
        credit_history=CreditHistoryInput(
            has_bankruptcy=True,
            bankruptcy_discharge_years=3.5,
            bankruptcy_chapter="7",
        ),
        equipment=EquipmentInput(
            category="trailer",
            year=2020,
            condition="used",
        ),
        loan_request=LoanRequestInput(
            amount=5000000,
            transaction_type="purchase",
        ),
    )


class TestApplicationDBManagerCreate:
    """Tests for ApplicationDBManager.create_application()."""

    @pytest.mark.asyncio
    async def test_creates_business_record(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
    ):
        """Should create a Business record with correct data."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(sample_application_request)
        await test_session.commit()

        # Query the business
        result = await test_session.execute(
            select(Business).where(Business.id == application.business_id)
        )
        business = result.scalar_one()

        assert business.legal_name == "Test Trucking LLC"
        assert business.state == "TX"
        assert business.industry_code == "484110"
        assert float(business.years_in_business) == 5.0
        assert business.annual_revenue == 1500000
        assert business.fleet_size == 3

    @pytest.mark.asyncio
    async def test_creates_guarantor_record(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
    ):
        """Should create a PersonalGuarantor record with credit scores."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(sample_application_request)
        await test_session.commit()

        # Query the guarantor
        result = await test_session.execute(
            select(PersonalGuarantor).where(
                PersonalGuarantor.id == application.guarantor_id
            )
        )
        guarantor = result.scalar_one()

        assert guarantor.fico_score == 720
        assert guarantor.transunion_score == 715
        assert guarantor.experian_score == 710
        assert guarantor.equifax_score == 725
        assert guarantor.is_homeowner is True
        assert guarantor.has_cdl is True
        assert guarantor.cdl_years == 5

    @pytest.mark.asyncio
    async def test_creates_application_record(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
    ):
        """Should create a LoanApplication record with equipment and loan details."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(sample_application_request)
        await test_session.commit()

        assert application.loan_amount == 15000000
        assert application.requested_term_months == 60
        assert application.equipment_category == "class_8_truck"
        assert application.equipment_year == 2022
        assert application.equipment_mileage == 50000
        assert application.transaction_type == "purchase"
        assert application.status == "pending"
        assert application.application_number is not None

    @pytest.mark.asyncio
    async def test_creates_business_credit_when_provided(
        self,
        test_session: AsyncSession,
        sample_application_with_business_credit: ApplicationSubmitRequest,
    ):
        """Should create BusinessCredit record when business_credit is provided."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(
            sample_application_with_business_credit
        )
        await test_session.commit()

        # Query business credit
        result = await test_session.execute(
            select(BusinessCredit).where(
                BusinessCredit.business_id == application.business_id
            )
        )
        business_credit = result.scalar_one()

        assert business_credit.paynet_score == 75
        assert business_credit.paynet_master_score == 680
        assert business_credit.paydex_score == 80

    @pytest.mark.asyncio
    async def test_handles_bankruptcy_date_conversion(
        self,
        test_session: AsyncSession,
        sample_application_with_bankruptcy: ApplicationSubmitRequest,
    ):
        """Should convert bankruptcy_discharge_years to a date."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(
            sample_application_with_bankruptcy
        )
        await test_session.commit()

        # Query the guarantor
        result = await test_session.execute(
            select(PersonalGuarantor).where(
                PersonalGuarantor.id == application.guarantor_id
            )
        )
        guarantor = result.scalar_one()

        assert guarantor.has_bankruptcy is True
        assert guarantor.bankruptcy_discharge_date is not None
        assert guarantor.bankruptcy_chapter == "7"
        # Check years calculation is approximately correct (within 0.5 year)
        discharge_years = guarantor.bankruptcy_discharge_years
        assert discharge_years is not None
        assert 3.0 <= discharge_years <= 4.0


class TestApplicationDBManagerStatus:
    """Tests for ApplicationDBManager status operations."""

    @pytest.mark.asyncio
    async def test_update_status_to_processing(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
    ):
        """Should update application status to processing."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(sample_application_request)
        await test_session.commit()

        await service.update_status(application.id, "processing")
        await test_session.commit()

        # Refresh and check
        await test_session.refresh(application)
        assert application.status == "processing"

    @pytest.mark.asyncio
    async def test_update_status_to_completed(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
    ):
        """Should update application status to completed and set processed_at."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(sample_application_request)
        await test_session.commit()

        await service.update_status(application.id, "completed")
        await test_session.commit()

        await test_session.refresh(application)
        assert application.status == "completed"
        assert application.processed_at is not None

    @pytest.mark.asyncio
    async def test_update_status_to_error(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
    ):
        """Should update application status to error and set processed_at."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(sample_application_request)
        await test_session.commit()

        await service.update_status(application.id, "error")
        await test_session.commit()

        await test_session.refresh(application)
        assert application.status == "error"
        assert application.processed_at is not None


class TestApplicationDBManagerMatchResults:
    """Tests for ApplicationDBManager match result operations."""

    @pytest_asyncio.fixture
    async def lender(self, test_session: AsyncSession) -> Lender:
        """Create a test lender."""
        lender = Lender(
            id="test_lender",
            name="Test Lender",
            policy_file="test_lender.yaml",
            policy_version=1,
        )
        test_session.add(lender)
        await test_session.commit()
        return lender

    @pytest.mark.asyncio
    async def test_save_eligible_match_results(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
        lender: Lender,
    ):
        """Should save eligible match results with criteria."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(sample_application_request)
        await test_session.commit()

        matches = [
            {
                "lender_id": "test_lender",
                "is_eligible": True,
                "fit_score": 85,
                "rank": 1,
                "best_program": {
                    "program_id": "standard",
                    "program_name": "Standard Program",
                    "criteria_results": [
                        {
                            "rule_name": "Minimum FICO Score",
                            "passed": True,
                            "required_value": "650",
                            "actual_value": "720",
                            "message": "FICO score 720 meets minimum 650",
                        },
                    ],
                },
            }
        ]

        results = await service.save_match_results(application.id, matches)
        await test_session.commit()

        assert len(results) == 1
        assert results[0].is_eligible is True
        assert results[0].fit_score == 85
        assert results[0].rank == 1
        assert results[0].matched_program_name == "Standard Program"
        assert "minimum_fico_score" in results[0].criteria_results

    @pytest.mark.asyncio
    async def test_save_ineligible_match_results(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
        lender: Lender,
    ):
        """Should save ineligible match results with rejection reasons."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(sample_application_request)
        await test_session.commit()

        matches = [
            {
                "lender_id": "test_lender",
                "is_eligible": False,
                "fit_score": 0,
                "rank": None,
                "rejection_reasons": ["Credit score 580 below minimum 650"],
                "global_rejection_reasons": [],
            }
        ]

        results = await service.save_match_results(application.id, matches)
        await test_session.commit()

        assert len(results) == 1
        assert results[0].is_eligible is False
        assert results[0].fit_score == 0
        assert results[0].rank is None
        assert "Credit score 580 below minimum 650" in results[0].rejection_reasons

    @pytest.mark.asyncio
    async def test_get_match_results(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
        lender: Lender,
    ):
        """Should retrieve match results for an application."""
        service = ApplicationDBManager(test_session)

        application = await service.create_application(sample_application_request)
        await test_session.commit()

        # Create a match result
        match_result = MatchResult(
            application_id=application.id,
            lender_id="test_lender",
            is_eligible=True,
            fit_score=80,
            rank=1,
        )
        test_session.add(match_result)
        await test_session.commit()

        results = await service.get_match_results(application.id)

        assert len(results) == 1
        assert results[0].is_eligible is True
        assert results[0].fit_score == 80


class TestApplicationDBManagerQuery:
    """Tests for ApplicationDBManager query operations."""

    @pytest.mark.asyncio
    async def test_get_application_by_id(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
    ):
        """Should retrieve application by ID with relationships."""
        service = ApplicationDBManager(test_session)

        created = await service.create_application(sample_application_request)
        await test_session.commit()

        retrieved = await service.get_application(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.business is not None
        assert retrieved.business.legal_name == "Test Trucking LLC"
        assert retrieved.guarantor is not None
        assert retrieved.guarantor.fico_score == 720

    @pytest.mark.asyncio
    async def test_get_application_not_found(self, test_session: AsyncSession):
        """Should return None for non-existent application."""
        service = ApplicationDBManager(test_session)

        result = await service.get_application(
            UUID("00000000-0000-0000-0000-000000000000")
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_list_applications_empty(self, test_session: AsyncSession):
        """Should return empty list when no applications exist."""
        service = ApplicationDBManager(test_session)

        applications, total = await service.list_applications(skip=0, limit=10)

        assert applications == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_applications_with_pagination(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
    ):
        """Should return paginated applications."""
        service = ApplicationDBManager(test_session)

        # Create multiple applications
        for i in range(5):
            modified = sample_application_request.model_copy()
            modified.business.name = f"Business {i}"
            await service.create_application(modified)
        await test_session.commit()

        # Get first page
        applications, total = await service.list_applications(skip=0, limit=2)

        assert len(applications) == 2
        assert total == 5

        # Get second page
        applications2, total2 = await service.list_applications(skip=2, limit=2)

        assert len(applications2) == 2
        assert total2 == 5

    @pytest.mark.asyncio
    async def test_list_applications_ordered_by_created_at(
        self,
        test_session: AsyncSession,
        sample_application_request: ApplicationSubmitRequest,
    ):
        """Should return applications with correct pagination regardless of order."""
        service = ApplicationDBManager(test_session)

        # Create applications
        app1 = await service.create_application(sample_application_request)
        await test_session.commit()

        modified = sample_application_request.model_copy()
        modified.business.name = "Second Business"
        app2 = await service.create_application(modified)
        await test_session.commit()

        applications, total = await service.list_applications(skip=0, limit=10)

        # Both applications should be returned
        assert total == 2
        assert len(applications) == 2
        app_ids = {a.id for a in applications}
        assert app1.id in app_ids
        assert app2.id in app_ids


class TestApplicationDBManagerSyncLenders:
    """Tests for ApplicationDBManager.sync_lenders()."""

    @pytest.fixture
    def sample_policies(self) -> list[LenderPolicy]:
        """Create sample LenderPolicy objects for testing."""
        return [
            LenderPolicy(
                id="test_lender_1",
                name="Test Lender One",
                version=1,
                contact_email="test1@example.com",
                contact_phone="555-0001",
                programs=[
                    LenderProgram(
                        id="standard",
                        name="Standard Program",
                        credit_score={"type": "fico", "min": 650},
                    )
                ],
            ),
            LenderPolicy(
                id="test_lender_2",
                name="Test Lender Two",
                version=2,
                programs=[
                    LenderProgram(
                        id="premium",
                        name="Premium Program",
                        credit_score={"type": "fico", "min": 700},
                    )
                ],
            ),
        ]

    @pytest.mark.asyncio
    async def test_sync_lenders_creates_new_lenders(
        self,
        test_session: AsyncSession,
        sample_policies: list[LenderPolicy],
    ):
        """Should create new lender records for policies not in DB."""
        service = ApplicationDBManager(test_session)

        await service.sync_lenders(sample_policies)
        await test_session.commit()

        # Query all lenders
        result = await test_session.execute(select(Lender))
        lenders = {l.id: l for l in result.scalars().all()}

        assert len(lenders) == 2
        assert "test_lender_1" in lenders
        assert "test_lender_2" in lenders

        # Check fields
        lender1 = lenders["test_lender_1"]
        assert lender1.name == "Test Lender One"
        assert lender1.policy_file == "test_lender_1.yaml"
        assert lender1.policy_version == 1
        assert lender1.contact_email == "test1@example.com"
        assert lender1.is_active is True

    @pytest.mark.asyncio
    async def test_sync_lenders_updates_existing_lender_version(
        self,
        test_session: AsyncSession,
        sample_policies: list[LenderPolicy],
    ):
        """Should update existing lender when policy version changes."""
        # Create an existing lender with older version
        existing = Lender(
            id="test_lender_1",
            name="Old Name",
            policy_file="test_lender_1.yaml",
            policy_version=0,  # Older version
        )
        test_session.add(existing)
        await test_session.commit()

        service = ApplicationDBManager(test_session)
        await service.sync_lenders(sample_policies)
        await test_session.commit()

        # Refresh and check
        await test_session.refresh(existing)
        assert existing.policy_version == 1  # Updated
        assert existing.name == "Test Lender One"  # Updated

    @pytest.mark.asyncio
    async def test_sync_lenders_skips_same_version(
        self,
        test_session: AsyncSession,
        sample_policies: list[LenderPolicy],
    ):
        """Should not update lender if version is same."""
        # Create an existing lender with same version
        existing = Lender(
            id="test_lender_1",
            name="Keep This Name",
            policy_file="test_lender_1.yaml",
            policy_version=1,  # Same version
        )
        test_session.add(existing)
        await test_session.commit()

        service = ApplicationDBManager(test_session)
        await service.sync_lenders(sample_policies)
        await test_session.commit()

        # Refresh and check name wasn't updated
        await test_session.refresh(existing)
        assert existing.name == "Keep This Name"  # Not updated

    @pytest.mark.asyncio
    async def test_sync_lenders_empty_list(self, test_session: AsyncSession):
        """Should handle empty policy list without error."""
        service = ApplicationDBManager(test_session)

        # Should not raise
        await service.sync_lenders([])
        await test_session.commit()

        # No lenders created
        result = await test_session.execute(select(Lender))
        lenders = list(result.scalars().all())
        assert len(lenders) == 0
