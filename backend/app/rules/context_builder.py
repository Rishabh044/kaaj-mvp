"""Context builder for transforming database models to EvaluationContext."""

from datetime import datetime
from typing import Any, Optional

from app.rules.base import EvaluationContext


def build_evaluation_context(
    application_id: str,
    business: Optional[dict[str, Any]] = None,
    guarantor: Optional[dict[str, Any]] = None,
    business_credit: Optional[dict[str, Any]] = None,
    loan_request: Optional[dict[str, Any]] = None,
    equipment: Optional[dict[str, Any]] = None,
    derived_features: Optional[dict[str, Any]] = None,
) -> EvaluationContext:
    """Assemble evaluation context from database model data.

    This function transforms the various domain models into a flat
    EvaluationContext that rules can easily access.

    Args:
        application_id: The unique application identifier.
        business: Business entity data (dict from model).
        guarantor: Personal guarantor data (dict from model).
        business_credit: Business credit data (dict from model).
        loan_request: Loan request data (dict).
        equipment: Equipment data (dict).
        derived_features: Pre-computed derived features that override
                         calculated values (e.g., equipment_age_years).

    Returns:
        Populated EvaluationContext ready for rule evaluation.
    """
    business = business or {}
    guarantor = guarantor or {}
    business_credit = business_credit or {}
    loan_request = loan_request or {}
    equipment = equipment or {}
    derived_features = derived_features or {}

    # Calculate equipment age if not provided
    equipment_year = equipment.get("year", 0)
    current_year = datetime.now().year
    equipment_age = derived_features.get(
        "equipment_age_years",
        max(0, current_year - equipment_year) if equipment_year else 0,
    )

    # Calculate years in business if not provided
    years_in_business = derived_features.get(
        "years_in_business", business.get("years_in_business", 0.0)
    )

    # Calculate bankruptcy discharge years if applicable
    bankruptcy_discharge_years = derived_features.get(
        "bankruptcy_discharge_years", guarantor.get("bankruptcy_discharge_years")
    )

    return EvaluationContext(
        # Application Reference
        application_id=application_id,
        # Credit Scores (Personal)
        fico_score=guarantor.get("fico_score"),
        transunion_score=guarantor.get("transunion_score"),
        experian_score=guarantor.get("experian_score"),
        equifax_score=guarantor.get("equifax_score"),
        # Credit Scores (Business)
        paynet_score=business_credit.get("paynet_score"),
        paynet_master_score=business_credit.get("paynet_master_score"),
        paydex_score=business_credit.get("paydex_score"),
        # Business Info
        business_name=business.get("name", ""),
        years_in_business=years_in_business,
        industry_code=business.get("industry_code", ""),
        industry_name=business.get("industry_name", ""),
        state=business.get("state", ""),
        annual_revenue=business.get("annual_revenue"),
        fleet_size=business.get("fleet_size"),
        # Guarantor Info
        is_homeowner=guarantor.get("is_homeowner", False),
        is_us_citizen=guarantor.get("is_us_citizen", True),
        has_cdl=guarantor.get("has_cdl", False),
        cdl_years=guarantor.get("cdl_years"),
        industry_experience_years=guarantor.get("industry_experience_years"),
        # Credit History
        has_bankruptcy=guarantor.get("has_bankruptcy", False),
        bankruptcy_discharge_years=bankruptcy_discharge_years,
        bankruptcy_chapter=guarantor.get("bankruptcy_chapter"),
        has_open_judgements=guarantor.get("has_open_judgements", False),
        judgement_amount=guarantor.get("judgement_amount"),
        has_foreclosure=guarantor.get("has_foreclosure", False),
        has_repossession=guarantor.get("has_repossession", False),
        has_tax_liens=guarantor.get("has_tax_liens", False),
        tax_lien_amount=guarantor.get("tax_lien_amount"),
        # Loan Request
        loan_amount=loan_request.get("loan_amount", 0),
        requested_term_months=loan_request.get("requested_term_months"),
        down_payment_percent=loan_request.get("down_payment_percent"),
        transaction_type=loan_request.get("transaction_type", "purchase"),
        is_private_party=loan_request.get("is_private_party", False),
        # Equipment
        equipment_category=equipment.get("category", ""),
        equipment_type=equipment.get("type", ""),
        equipment_year=equipment_year,
        equipment_age_years=equipment_age,
        equipment_mileage=equipment.get("mileage"),
        equipment_hours=equipment.get("hours"),
        equipment_condition=equipment.get("condition", "used"),
    )
