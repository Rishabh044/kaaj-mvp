"""Application service for managing loan application persistence using SQLAlchemy."""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import LoanApplication
from app.models.business import Business
from app.models.business_credit import BusinessCredit
from app.models.guarantor import PersonalGuarantor
from app.models.lender import Lender
from app.models.match_result import MatchResult
from app.policies.schema import LenderPolicy
from app.schemas.api import ApplicationSubmitRequest


class ApplicationDBManager:
    """Service for managing loan application persistence using SQLAlchemy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_application(
        self, input: ApplicationSubmitRequest
    ) -> LoanApplication:
        """Create Business, PersonalGuarantor, BusinessCredit, LoanApplication records.

        Uses SQLAlchemy ORM to create and add records to the session.
        Record creation order (respecting foreign keys):
        1. Business -> 2. PersonalGuarantor -> 3. BusinessCredit -> 4. LoanApplication
        """
        # Create Business
        business = Business(
            legal_name=input.business.name,
            entity_type="LLC",
            industry_code=input.business.industry_code or "",
            industry_name=input.business.industry_name or "",
            state=input.business.state,
            city="",
            zip_code="",
            years_in_business=input.business.years_in_business,
            annual_revenue=input.business.annual_revenue,
            fleet_size=input.business.fleet_size,
        )
        self.db.add(business)
        await self.db.flush()  # Get business.id

        # Create PersonalGuarantor
        # Calculate bankruptcy_discharge_date from years if provided
        bankruptcy_discharge_date = None
        if (
            input.credit_history.has_bankruptcy
            and input.credit_history.bankruptcy_discharge_years is not None
        ):
            days_ago = int(input.credit_history.bankruptcy_discharge_years * 365.25)
            bankruptcy_discharge_date = date.today() - timedelta(days=days_ago)

        guarantor = PersonalGuarantor(
            first_name="Applicant",
            last_name="Unknown",
            fico_score=input.applicant.fico_score,
            transunion_score=input.applicant.transunion_score,
            experian_score=input.applicant.experian_score,
            equifax_score=input.applicant.equifax_score,
            is_homeowner=input.applicant.is_homeowner,
            is_us_citizen=input.applicant.is_us_citizen,
            has_cdl=input.applicant.has_cdl,
            cdl_years=input.applicant.cdl_years,
            industry_experience_years=input.applicant.industry_experience_years,
            has_bankruptcy=input.credit_history.has_bankruptcy,
            bankruptcy_discharge_date=bankruptcy_discharge_date,
            bankruptcy_chapter=input.credit_history.bankruptcy_chapter,
            has_foreclosure=input.credit_history.has_foreclosure,
            has_repossession=input.credit_history.has_repossession,
            has_tax_liens=input.credit_history.has_tax_liens,
            tax_lien_amount=input.credit_history.tax_lien_amount,
            has_open_judgements=input.credit_history.has_open_judgements,
            judgement_amount=input.credit_history.judgement_amount,
        )
        self.db.add(guarantor)
        await self.db.flush()  # Get guarantor.id

        # Create BusinessCredit (optional)
        if input.business_credit:
            business_credit = BusinessCredit(
                business_id=business.id,
                paynet_score=input.business_credit.paynet_score,
                paynet_master_score=input.business_credit.paynet_master_score,
                paydex_score=input.business_credit.paydex_score,
            )
            self.db.add(business_credit)

        # Create LoanApplication
        application = LoanApplication(
            business_id=business.id,
            guarantor_id=guarantor.id,
            loan_amount=input.loan_request.amount,
            requested_term_months=input.loan_request.requested_term_months,
            down_payment_percent=input.loan_request.down_payment_percent,
            transaction_type=input.loan_request.transaction_type,
            is_private_party=input.loan_request.is_private_party,
            equipment_category=input.equipment.category,
            equipment_type=input.equipment.type or "",
            equipment_year=input.equipment.year,
            equipment_mileage=input.equipment.mileage,
            equipment_hours=input.equipment.hours,
            equipment_condition=input.equipment.condition,
            status="pending",
        )
        application.update_equipment_age()
        self.db.add(application)
        await self.db.flush()  # Get application.id and application_number

        return application

    async def update_status(self, application_id: UUID, status: str) -> None:
        """Update application status using SQLAlchemy."""
        stmt = select(LoanApplication).where(LoanApplication.id == application_id)
        result = await self.db.execute(stmt)
        app = result.scalar_one_or_none()
        if app:
            if status == "processing":
                app.mark_processing()
            elif status == "completed":
                app.mark_completed()
            elif status == "error":
                app.mark_error()

    async def sync_lenders(self, policies: list[LenderPolicy]) -> None:
        """Ensure all lenders from policies exist in database.

        This must be called before saving match results to avoid foreign key
        constraint violations. Performs upsert: creates new lenders or updates
        existing ones if policy version changed.
        """
        for policy in policies:
            stmt = select(Lender).where(Lender.id == policy.id)
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                lender = Lender(
                    id=policy.id,
                    name=policy.name,
                    is_active=True,
                    policy_file=f"{policy.id}.yaml",
                    policy_version=policy.version,
                    contact_email=policy.contact_email,
                    contact_phone=policy.contact_phone,
                )
                self.db.add(lender)
            elif existing.policy_version != policy.version:
                existing.policy_version = policy.version
                existing.name = policy.name

        await self.db.flush()

    async def save_match_results(
        self, application_id: UUID, matches: list[dict]
    ) -> list[MatchResult]:
        """Persist MatchResult records using SQLAlchemy ORM."""
        results = []
        for match in matches:
            match_result = MatchResult(
                application_id=application_id,
                lender_id=match["lender_id"],
                is_eligible=match["is_eligible"],
                fit_score=int(match.get("fit_score", 0)),
                rank=match.get("rank"),
                matched_program_id=(
                    match.get("best_program", {}).get("program_id")
                    if match.get("best_program")
                    else None
                ),
                matched_program_name=(
                    match.get("best_program", {}).get("program_name")
                    if match.get("best_program")
                    else None
                ),
                criteria_results=self._build_criteria_json(match),
                rejection_reasons=(
                    match.get("rejection_reasons")
                    or match.get("global_rejection_reasons", [])
                ),
            )
            self.db.add(match_result)
            results.append(match_result)
        await self.db.flush()
        return results

    async def get_application(self, application_id: UUID) -> Optional[LoanApplication]:
        """Retrieve application with eager-loaded relationships using selectinload."""
        stmt = (
            select(LoanApplication)
            .options(
                selectinload(LoanApplication.business),
                selectinload(LoanApplication.guarantor),
            )
            .where(LoanApplication.id == application_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_applications(
        self, skip: int, limit: int
    ) -> tuple[list[LoanApplication], int]:
        """List applications with pagination using SQLAlchemy."""
        # Count total
        count_stmt = select(func.count()).select_from(LoanApplication)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Fetch page with eager loading
        stmt = (
            select(LoanApplication)
            .options(selectinload(LoanApplication.business))
            .order_by(LoanApplication.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        applications = list(result.scalars().all())

        return applications, total

    async def get_match_results(self, application_id: UUID) -> list[MatchResult]:
        """Retrieve match results using SQLAlchemy with lender eager loading."""
        stmt = (
            select(MatchResult)
            .options(selectinload(MatchResult.lender))
            .where(MatchResult.application_id == application_id)
            .order_by(MatchResult.rank.nulls_last())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _build_criteria_json(self, match: dict) -> dict:
        """Transform criteria_results list to JSONB-compatible dict."""
        result = {}
        best_program = match.get("best_program") or {}
        criteria_list = best_program.get("criteria_results", [])

        for cr in criteria_list:
            key = cr.get("rule_name", "unknown").lower().replace(" ", "_")
            result[key] = {
                "passed": cr.get("passed", False),
                "rule_name": cr.get("rule_name", ""),
                "required_value": str(cr.get("required_value", "")),
                "actual_value": str(cr.get("actual_value", "")),
                "message": cr.get("message", ""),
            }

        return result
