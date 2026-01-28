# Lender Matching Platform - Implementation Plan

## Overview

Build an extensible loan underwriting and lender matching system that evaluates business loan applications against multiple lenders' credit policies.

**Key Goals:**
- Normalized data models for applications, lenders, and match results
- Rule engine that evaluates applications against lender criteria
- Hatchet workflow with parallelization and retry logic
- Web UI for application submission, results viewing, and policy management

**Tech Stack:** FastAPI (backend), React TypeScript (frontend), PostgreSQL, Hatchet (workflows)

---

## Data Models

### Entity Relationship Diagram

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   LoanApplication   │────▶│  PersonalGuarantor  │     │    BusinessCredit   │
│  (main application) │     │   (credit profile)  │     │  (PayNet, trades)   │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
          │                           │                           │
          │                           └───────────┬───────────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────────┐     ┌─────────────────────────────────────────────────┐
│    MatchResult      │────▶│              EvaluationContext                  │
│  (persisted result) │     │        (assembled for rule evaluation)          │
└─────────────────────┘     └─────────────────────────────────────────────────┘
          │                                       │
          │                                       ▼
          │                 ┌─────────────────────────────────────────────────┐
          │                 │               Lender Policies                   │
          │                 │  (YAML files + DB metadata for UI management)   │
          └────────────────▶└─────────────────────────────────────────────────┘
```

### 1. Borrower/Business

Represents the business applying for financing.

```python
class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Basic Info
    legal_name: Mapped[str] = mapped_column(String(255))
    dba_name: Mapped[Optional[str]] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(50))  # LLC, Corp, Sole Prop

    # Industry
    industry_code: Mapped[str] = mapped_column(String(10))  # NAICS or SIC
    industry_name: Mapped[str] = mapped_column(String(255))

    # Location
    state: Mapped[str] = mapped_column(String(2))
    city: Mapped[str] = mapped_column(String(100))
    zip_code: Mapped[str] = mapped_column(String(10))

    # Business Metrics
    years_in_business: Mapped[float] = mapped_column(Numeric(4, 1))
    annual_revenue: Mapped[Optional[int]] = mapped_column(BigInteger)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Trucking-Specific
    fleet_size: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    # Relationships
    loan_applications: Mapped[list["LoanApplication"]] = relationship(back_populates="business")
```

### 2. Personal Guarantor

Represents the individual guaranteeing the loan with their credit profile.

```python
class PersonalGuarantor(Base):
    __tablename__ = "personal_guarantors"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Identity
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    ssn_last_four: Mapped[Optional[str]] = mapped_column(String(4))  # For reference only

    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Credit Scores
    fico_score: Mapped[Optional[int]] = mapped_column(Integer)
    transunion_score: Mapped[Optional[int]] = mapped_column(Integer)
    experian_score: Mapped[Optional[int]] = mapped_column(Integer)
    equifax_score: Mapped[Optional[int]] = mapped_column(Integer)

    # Homeownership
    is_homeowner: Mapped[bool] = mapped_column(Boolean, default=False)

    # Citizenship
    is_us_citizen: Mapped[bool] = mapped_column(Boolean, default=True)

    # Credit History Flags
    has_bankruptcy: Mapped[bool] = mapped_column(Boolean, default=False)
    bankruptcy_discharge_date: Mapped[Optional[date]] = mapped_column(Date)
    bankruptcy_chapter: Mapped[Optional[str]] = mapped_column(String(10))  # 7, 11, 13

    has_open_judgements: Mapped[bool] = mapped_column(Boolean, default=False)
    judgement_amount: Mapped[Optional[int]] = mapped_column(Integer)

    has_foreclosure: Mapped[bool] = mapped_column(Boolean, default=False)
    foreclosure_date: Mapped[Optional[date]] = mapped_column(Date)

    has_repossession: Mapped[bool] = mapped_column(Boolean, default=False)
    repossession_date: Mapped[Optional[date]] = mapped_column(Date)

    has_tax_liens: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_lien_amount: Mapped[Optional[int]] = mapped_column(Integer)

    # Professional (for trucking)
    has_cdl: Mapped[bool] = mapped_column(Boolean, default=False)
    cdl_years: Mapped[Optional[int]] = mapped_column(Integer)
    industry_experience_years: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    loan_applications: Mapped[list["LoanApplication"]] = relationship(back_populates="guarantor")
```

### 3. Business Credit

Represents business credit profile (PayNet, trade lines).

```python
class BusinessCredit(Base):
    __tablename__ = "business_credits"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"))

    # PayNet Score
    paynet_score: Mapped[Optional[int]] = mapped_column(Integer)
    paynet_master_score: Mapped[Optional[int]] = mapped_column(Integer)

    # D&B
    duns_number: Mapped[Optional[str]] = mapped_column(String(9))
    dnb_rating: Mapped[Optional[str]] = mapped_column(String(10))
    paydex_score: Mapped[Optional[int]] = mapped_column(Integer)

    # Trade Lines
    trade_line_count: Mapped[Optional[int]] = mapped_column(Integer)
    highest_credit: Mapped[Optional[int]] = mapped_column(Integer)
    average_days_to_pay: Mapped[Optional[int]] = mapped_column(Integer)

    # Negative Items
    has_slow_pays: Mapped[bool] = mapped_column(Boolean, default=False)
    slow_pay_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamps
    report_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    business: Mapped["Business"] = relationship(back_populates="business_credit")
```

### 4. Loan Request & Equipment

Represents the loan request with equipment details.

```python
class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_number: Mapped[str] = mapped_column(String(20), unique=True)

    # Foreign Keys
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"))
    guarantor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("personal_guarantors.id"))

    # Loan Details
    loan_amount: Mapped[int] = mapped_column(Integer)  # In cents for precision
    requested_term_months: Mapped[Optional[int]] = mapped_column(Integer)
    down_payment_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    # Transaction Type
    transaction_type: Mapped[str] = mapped_column(String(50))  # purchase, refinance, sale_leaseback
    is_private_party: Mapped[bool] = mapped_column(Boolean, default=False)

    # Equipment Details
    equipment_category: Mapped[str] = mapped_column(String(100))  # class_8_truck, trailer, construction
    equipment_type: Mapped[str] = mapped_column(String(100))  # specific type
    equipment_make: Mapped[Optional[str]] = mapped_column(String(100))
    equipment_model: Mapped[Optional[str]] = mapped_column(String(100))
    equipment_year: Mapped[int] = mapped_column(Integer)
    equipment_mileage: Mapped[Optional[int]] = mapped_column(Integer)
    equipment_hours: Mapped[Optional[int]] = mapped_column(Integer)  # For construction equipment

    # Derived Fields (computed on save)
    equipment_age_years: Mapped[int] = mapped_column(Integer)  # Current year - equipment year

    # Equipment Condition
    equipment_condition: Mapped[str] = mapped_column(String(20))  # new, used, certified

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processing, completed, error

    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    # Relationships
    business: Mapped["Business"] = relationship(back_populates="loan_applications")
    guarantor: Mapped["PersonalGuarantor"] = relationship(back_populates="loan_applications")
    match_results: Mapped[list["MatchResult"]] = relationship(back_populates="application")
```

### 5. Lender Policies (Hybrid: YAML + Database)

**Database Model** (for UI management):

```python
class Lender(Base):
    __tablename__ = "lenders"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g., "citizens_bank"

    # Display Info
    name: Mapped[str] = mapped_column(String(255))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Contact
    contact_name: Mapped[Optional[str]] = mapped_column(String(100))
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Policy File Reference
    policy_file: Mapped[str] = mapped_column(String(255))  # Path to YAML file
    policy_version: Mapped[int] = mapped_column(Integer, default=1)
    policy_last_updated: Mapped[datetime] = mapped_column(default=func.now())

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    # Relationships
    match_results: Mapped[list["MatchResult"]] = relationship(back_populates="lender")
```

**YAML Policy Schema** (for rule definitions):

```yaml
# policies/lenders/citizens_bank.yaml
id: citizens_bank
name: Citizens Bank
version: 1
last_updated: "2025-01-15"

# Contact Information
contact:
  name: Joey Walter
  email: joey.walter@thecitizensbank.net
  phone: "501-451-5113"

# Programs/Tiers
programs:
  - id: tier_1_app_only
    name: Tier 1 - App Only
    description: "Quick approval up to $75K for established businesses"
    is_app_only: true
    min_amount: 10000
    max_amount: 75000

    # Eligibility Criteria
    criteria:
      credit_score:
        type: transunion  # or fico, paynet
        min: 700

      business:
        min_time_in_business_years: 2
        requires_homeowner: true
        requires_cdl: conditional  # Required if trucking

      credit_history:
        max_bankruptcies: 0
        bankruptcy_min_discharge_years: 5  # If had one
        max_open_judgements: 0
        max_tax_liens: 0

      documentation:
        required:
          - bank_statements_months: 3

  - id: tier_2_startup
    name: Tier 2 - Startup Program
    description: "For new businesses with experienced operators"
    is_app_only: true
    min_amount: 10000
    max_amount: 50000

    criteria:
      credit_score:
        type: transunion
        min: 700

      business:
        min_time_in_business_years: 0  # Startups OK
        min_cdl_years: 5
        min_industry_experience_years: 5
        requires_homeowner: true

  - id: tier_3_full_doc
    name: Tier 3 - Full Documentation
    description: "Larger deals requiring full financials"
    is_app_only: false
    min_amount: 75001
    max_amount: 1000000

    criteria:
      credit_score:
        type: transunion
        min: 680

      business:
        min_time_in_business_years: 2
        min_annual_revenue: 500000

      documentation:
        required:
          - tax_returns_years: 2
          - financial_statements: true
          - bank_statements_months: 3

# Equipment Term Matrices
equipment_matrices:
  class_8_truck:
    lookup_field: mileage
    entries:
      - max: 200000
        max_term_months: 60
      - min: 200001
        max: 400000
        max_term_months: 48
      - min: 400001
        max: 600000
        max_term_months: 36
      - min: 600001
        max_term_months: 0  # Not desired
        rejection_reason: "Mileage exceeds 600,000 - not desired"

  trailer:
    lookup_field: age
    entries:
      - max: 5
        max_term_months: 60
      - min: 6
        max: 10
        max_term_months: 48
      - min: 11
        max_term_months: 0
        rejection_reason: "Trailer age exceeds 10 years"

# Restrictions
restrictions:
  # Geographic
  excluded_states:
    - CA
    - NY

  # Industry
  excluded_industries:
    - cannabis
    - gambling
    - adult_entertainment
    - firearms

  # Transaction Types
  transaction_types:
    purchase: true
    refinance: false
    sale_leaseback: false
    private_party: true

  # Other
  requires_us_citizen: true

# Scoring Weights (for fit score calculation)
scoring:
  weights:
    credit_score: 30
    time_in_business: 20
    loan_to_value: 15
    equipment_age: 15
    credit_history: 20
```

### 6. Match Results

Persists evaluation results for audit trail and display.

```python
class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loan_applications.id"))
    lender_id: Mapped[str] = mapped_column(ForeignKey("lenders.id"))

    # Eligibility
    is_eligible: Mapped[bool] = mapped_column(Boolean)
    matched_program_id: Mapped[Optional[str]] = mapped_column(String(50))
    matched_program_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Scoring
    fit_score: Mapped[int] = mapped_column(Integer)  # 0-100
    rank: Mapped[Optional[int]] = mapped_column(Integer)  # 1 = best match

    # Detailed Results (JSON)
    criteria_results: Mapped[dict] = mapped_column(JSON)
    # Structure:
    # {
    #   "credit_score": {
    #     "passed": false,
    #     "rule_name": "Minimum TransUnion Score",
    #     "required_value": 700,
    #     "actual_value": 650,
    #     "message": "TransUnion score 650 below minimum 700",
    #     "score_contribution": 0
    #   },
    #   "time_in_business": {
    #     "passed": true,
    #     "rule_name": "Minimum Time in Business",
    #     "required_value": "2 years",
    #     "actual_value": "5 years",
    #     "message": "Time in business 5 years exceeds minimum 2 years",
    #     "score_contribution": 20
    #   }
    # }

    # Summary
    rejection_reasons: Mapped[Optional[list]] = mapped_column(JSON)
    # ["Credit score 650 below minimum 700", "State CA is restricted"]

    # Timestamps
    evaluated_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    application: Mapped["LoanApplication"] = relationship(back_populates="match_results")
    lender: Mapped["Lender"] = relationship(back_populates="match_results")
```

---

## Core Architecture

### System Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│  ┌─────────────┐  ┌─────────────────┐  ┌───────────────────────────────┐   │
│  │ Application │  │ Results Display │  │ Lender Policy Management     │   │
│  │    Form     │  │  with Details   │  │  (View/Edit/Add Policies)    │   │
│  └──────┬──────┘  └────────▲────────┘  └───────────────────────────────┘   │
└─────────┼──────────────────┼───────────────────────────────────────────────┘
          │                  │
          ▼                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│  POST /applications    GET /applications/{id}/results    CRUD /lenders      │
└─────────┬──────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HATCHET WORKFLOW                                     │
│  ┌────────────┐   ┌────────────┐   ┌────────────────────┐   ┌────────────┐ │
│  │  Validate  │──▶│  Derive    │──▶│ Evaluate Lenders   │──▶│  Persist   │ │
│  │Application │   │  Features  │   │   (Parallel)       │   │  Results   │ │
│  └────────────┘   └────────────┘   └────────────────────┘   └────────────┘ │
│                                             │                               │
│                          ┌──────────────────┼──────────────────┐            │
│                          ▼                  ▼                  ▼            │
│                   ┌───────────┐      ┌───────────┐      ┌───────────┐      │
│                   │ Citizens  │      │  Stearns  │      │   Apex    │      │
│                   │   Bank    │      │   Bank    │      │Commercial │      │
│                   └───────────┘      └───────────┘      └───────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RULE ENGINE                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Policy Loader (YAML Files)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Rule Registry (Extensible)                        │   │
│  │  credit_score | business | equipment | geographic | credit_history  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Matching Engine                                   │   │
│  │  For each lender: Eligibility → Program Match → Score → Reasons     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE                                           │
│  Applications | Businesses | Guarantors | BusinessCredits | MatchResults    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Hatchet Workflow Design

### Workflow: Application Evaluation

```python
from hatchet_sdk import Hatchet, Context

hatchet = Hatchet()

@hatchet.workflow(name="application-evaluation", on_events=["application:submitted"])
class ApplicationEvaluationWorkflow:
    """
    Main workflow for evaluating a loan application against all lenders.
    Demonstrates: parallelization, retry logic, error handling.
    """

    @hatchet.step(timeout="30s", retries=3)
    async def validate_application(self, context: Context) -> dict:
        """
        Step 1: Validate that application has all required fields.

        Retries: 3 times on transient errors (e.g., DB connection)
        """
        application_id = context.workflow_input()["application_id"]

        async with get_db_session() as db:
            application = await get_application_with_relations(db, application_id)

            validation_errors = []

            # Required fields
            if not application.guarantor.fico_score:
                validation_errors.append("FICO score is required")
            if not application.business.state:
                validation_errors.append("Business state is required")
            if not application.loan_amount:
                validation_errors.append("Loan amount is required")
            if not application.equipment_category:
                validation_errors.append("Equipment category is required")

            if validation_errors:
                await update_application_status(db, application_id, "validation_failed")
                return {
                    "valid": False,
                    "errors": validation_errors
                }

            return {
                "valid": True,
                "application_id": str(application_id)
            }

    @hatchet.step(timeout="30s", parents=["validate_application"])
    async def derive_features(self, context: Context) -> dict:
        """
        Step 2: Compute derived features for evaluation.

        Examples:
        - Equipment age from year
        - Years since bankruptcy discharge
        - Business type classification
        """
        validation_result = context.step_output("validate_application")

        if not validation_result["valid"]:
            return {"skipped": True, "reason": "Validation failed"}

        application_id = validation_result["application_id"]

        async with get_db_session() as db:
            application = await get_application_with_relations(db, application_id)
            current_year = datetime.now().year

            derived = {
                # Equipment age
                "equipment_age_years": current_year - application.equipment_year,

                # Bankruptcy years since discharge
                "bankruptcy_discharge_years": None,

                # Business classification
                "is_startup": application.business.years_in_business < 2,
                "is_trucking": application.equipment_category in ["class_8_truck", "trailer", "semi"],
            }

            if application.guarantor.bankruptcy_discharge_date:
                days_since = (datetime.now().date() - application.guarantor.bankruptcy_discharge_date).days
                derived["bankruptcy_discharge_years"] = days_since / 365.25

            # Persist derived features
            await update_application_derived_features(db, application_id, derived)

            return {
                "application_id": application_id,
                "derived_features": derived
            }

    @hatchet.step(timeout="2m", parents=["derive_features"], retries=2)
    async def evaluate_all_lenders(self, context: Context) -> dict:
        """
        Step 3: Evaluate application against ALL active lenders in PARALLEL.

        Uses Hatchet's built-in concurrency for parallel evaluation.
        Retries: 2 times on failure.
        """
        derived_result = context.step_output("derive_features")

        if derived_result.get("skipped"):
            return {"skipped": True}

        application_id = derived_result["application_id"]

        async with get_db_session() as db:
            # Load application and build evaluation context
            application = await get_application_with_relations(db, application_id)
            evaluation_context = build_evaluation_context(application, derived_result["derived_features"])

            # Load all active lenders
            lenders = policy_loader.get_active_lenders()

            # Evaluate in parallel using asyncio.gather
            evaluation_tasks = [
                evaluate_single_lender(evaluation_context, lender)
                for lender in lenders
            ]

            results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)

            # Process results
            lender_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Log error but continue with other lenders
                    logger.error(f"Error evaluating lender {lenders[i].id}: {result}")
                    lender_results.append({
                        "lender_id": lenders[i].id,
                        "error": str(result),
                        "is_eligible": False
                    })
                else:
                    lender_results.append(result)

            return {
                "application_id": application_id,
                "lender_results": lender_results
            }

    @hatchet.step(timeout="30s", parents=["evaluate_all_lenders"], retries=3)
    async def persist_and_rank_results(self, context: Context) -> dict:
        """
        Step 4: Persist all match results and compute final ranking.

        Retries: 3 times for DB operations.
        """
        eval_result = context.step_output("evaluate_all_lenders")

        if eval_result.get("skipped"):
            return {"skipped": True}

        application_id = eval_result["application_id"]
        lender_results = eval_result["lender_results"]

        async with get_db_session() as db:
            # Sort by eligibility first, then by fit score
            sorted_results = sorted(
                lender_results,
                key=lambda x: (x.get("is_eligible", False), x.get("fit_score", 0)),
                reverse=True
            )

            # Assign ranks and persist
            match_results = []
            for rank, result in enumerate(sorted_results, 1):
                if result.get("error"):
                    continue

                match_result = MatchResult(
                    application_id=uuid.UUID(application_id),
                    lender_id=result["lender_id"],
                    is_eligible=result["is_eligible"],
                    matched_program_id=result.get("matched_program_id"),
                    matched_program_name=result.get("matched_program_name"),
                    fit_score=result.get("fit_score", 0),
                    rank=rank if result["is_eligible"] else None,
                    criteria_results=result.get("criteria_results", {}),
                    rejection_reasons=result.get("rejection_reasons", [])
                )
                db.add(match_result)
                match_results.append(match_result)

            # Update application status
            await update_application_status(db, application_id, "completed")
            await db.commit()

            eligible_count = sum(1 for r in lender_results if r.get("is_eligible"))

            return {
                "application_id": application_id,
                "total_lenders": len(lender_results),
                "eligible_count": eligible_count,
                "best_match_lender": sorted_results[0]["lender_id"] if eligible_count > 0 else None,
                "best_match_score": sorted_results[0]["fit_score"] if eligible_count > 0 else None
            }
```

### Workflow: Trigger on Application Submit

```python
# In API endpoint
@router.post("/applications", response_model=ApplicationResponse)
async def submit_application(
    application_input: LoanApplicationInput,
    db: DbSession,
    hatchet_client: HatchetClient = Depends(get_hatchet)
):
    # Create application in database
    application = await create_application(db, application_input)

    # Trigger Hatchet workflow
    workflow_run = await hatchet_client.admin.run_workflow(
        "application-evaluation",
        input={"application_id": str(application.id)}
    )

    return ApplicationResponse(
        id=application.id,
        application_number=application.application_number,
        status="processing",
        workflow_run_id=workflow_run.workflow_run_id
    )
```

---

## Matching Engine Design

### Evaluation Context Builder

```python
@dataclass
class EvaluationContext:
    """All data needed for rule evaluation, assembled from database models."""

    # Application Reference
    application_id: str

    # Credit Scores (Personal)
    fico_score: Optional[int]
    transunion_score: Optional[int]
    experian_score: Optional[int]
    equifax_score: Optional[int]

    # Credit Scores (Business)
    paynet_score: Optional[int]
    paynet_master_score: Optional[int]
    paydex_score: Optional[int]

    # Business Info
    business_name: str
    years_in_business: float
    industry_code: str
    industry_name: str
    state: str
    annual_revenue: Optional[int]
    fleet_size: Optional[int]

    # Guarantor Info
    is_homeowner: bool
    is_us_citizen: bool
    has_cdl: bool
    cdl_years: Optional[int]
    industry_experience_years: Optional[int]

    # Credit History
    has_bankruptcy: bool
    bankruptcy_discharge_years: Optional[float]
    bankruptcy_chapter: Optional[str]
    has_open_judgements: bool
    judgement_amount: Optional[int]
    has_foreclosure: bool
    has_repossession: bool
    has_tax_liens: bool
    tax_lien_amount: Optional[int]

    # Loan Request
    loan_amount: int
    requested_term_months: Optional[int]
    down_payment_percent: Optional[float]
    transaction_type: str
    is_private_party: bool

    # Equipment
    equipment_category: str
    equipment_type: str
    equipment_year: int
    equipment_age_years: int
    equipment_mileage: Optional[int]
    equipment_hours: Optional[int]
    equipment_condition: str


def build_evaluation_context(
    application: LoanApplication,
    derived_features: dict
) -> EvaluationContext:
    """Build evaluation context from database models."""
    return EvaluationContext(
        application_id=str(application.id),

        # Credit scores from guarantor
        fico_score=application.guarantor.fico_score,
        transunion_score=application.guarantor.transunion_score,
        experian_score=application.guarantor.experian_score,
        equifax_score=application.guarantor.equifax_score,

        # Business credit (if available)
        paynet_score=application.business.business_credit.paynet_score if application.business.business_credit else None,
        paynet_master_score=application.business.business_credit.paynet_master_score if application.business.business_credit else None,
        paydex_score=application.business.business_credit.paydex_score if application.business.business_credit else None,

        # Business info
        business_name=application.business.legal_name,
        years_in_business=float(application.business.years_in_business),
        industry_code=application.business.industry_code,
        industry_name=application.business.industry_name,
        state=application.business.state,
        annual_revenue=application.business.annual_revenue,
        fleet_size=application.business.fleet_size,

        # ... rest of fields from models and derived features
        equipment_age_years=derived_features["equipment_age_years"],
        # etc.
    )
```

### Rule Evaluation with Detailed Results

```python
class MatchingEngine:
    """Evaluates applications against lender policies."""

    def __init__(self, rule_registry: RuleRegistry):
        self.rule_registry = rule_registry

    async def evaluate_lender(
        self,
        context: EvaluationContext,
        lender_policy: LenderPolicy
    ) -> LenderMatchResult:
        """
        Evaluate application against a single lender.

        Returns:
            LenderMatchResult with:
            - is_eligible: bool
            - matched_program_id: str (if eligible)
            - matched_program_name: str (if eligible)
            - fit_score: 0-100
            - criteria_results: dict with detailed pass/fail for each criterion
            - rejection_reasons: list of human-readable reasons
        """
        criteria_results = {}
        rejection_reasons = []

        # First check hard restrictions (state, industry, transaction type)
        restriction_result = self._evaluate_restrictions(context, lender_policy)
        if not restriction_result.passed:
            return LenderMatchResult(
                lender_id=lender_policy.id,
                is_eligible=False,
                fit_score=0,
                criteria_results=restriction_result.details,
                rejection_reasons=restriction_result.reasons
            )

        # Evaluate each program to find best match
        best_program = None
        best_score = 0
        best_criteria_results = {}

        for program in lender_policy.programs:
            program_result = await self._evaluate_program(context, program, lender_policy)

            if program_result.is_eligible and program_result.fit_score > best_score:
                best_program = program
                best_score = program_result.fit_score
                best_criteria_results = program_result.criteria_results

        if best_program:
            return LenderMatchResult(
                lender_id=lender_policy.id,
                is_eligible=True,
                matched_program_id=best_program.id,
                matched_program_name=best_program.name,
                fit_score=best_score,
                criteria_results=best_criteria_results,
                rejection_reasons=[]
            )

        # No eligible program - compile all rejection reasons
        all_criteria_results = {}
        all_rejection_reasons = []

        for program in lender_policy.programs:
            program_result = await self._evaluate_program(context, program, lender_policy)
            all_criteria_results[program.id] = program_result.criteria_results
            all_rejection_reasons.extend(program_result.rejection_reasons)

        return LenderMatchResult(
            lender_id=lender_policy.id,
            is_eligible=False,
            fit_score=0,
            criteria_results=all_criteria_results,
            rejection_reasons=list(set(all_rejection_reasons))  # Deduplicate
        )

    async def _evaluate_program(
        self,
        context: EvaluationContext,
        program: LenderProgram,
        lender_policy: LenderPolicy
    ) -> ProgramEvaluationResult:
        """Evaluate application against a specific program."""

        criteria_results = {}
        rejection_reasons = []
        total_score = 0
        is_eligible = True

        # Check loan amount bounds
        if program.min_amount and context.loan_amount < program.min_amount:
            criteria_results["loan_amount"] = {
                "passed": False,
                "rule_name": "Minimum Loan Amount",
                "required_value": f"${program.min_amount:,}",
                "actual_value": f"${context.loan_amount:,}",
                "message": f"Loan amount ${context.loan_amount:,} below program minimum ${program.min_amount:,}",
                "score_contribution": 0
            }
            is_eligible = False
            rejection_reasons.append(f"Loan amount ${context.loan_amount:,} below minimum ${program.min_amount:,}")

        if program.max_amount and context.loan_amount > program.max_amount:
            criteria_results["loan_amount"] = {
                "passed": False,
                "rule_name": "Maximum Loan Amount",
                "required_value": f"${program.max_amount:,}",
                "actual_value": f"${context.loan_amount:,}",
                "message": f"Loan amount ${context.loan_amount:,} exceeds program maximum ${program.max_amount:,}",
                "score_contribution": 0
            }
            is_eligible = False
            rejection_reasons.append(f"Loan amount ${context.loan_amount:,} exceeds maximum ${program.max_amount:,}")

        # Evaluate each criterion type
        for criterion_type, criterion_config in program.criteria.items():
            rule = self.rule_registry.get_rule(criterion_type)

            if not rule:
                continue

            result = rule.evaluate(context, criterion_config)

            criteria_results[criterion_type] = {
                "passed": result.passed,
                "rule_name": result.rule_name,
                "required_value": result.required_value,
                "actual_value": result.actual_value,
                "message": result.message,
                "score_contribution": result.score if result.passed else 0
            }

            if not result.passed:
                is_eligible = False
                rejection_reasons.append(result.message)
            else:
                total_score += result.score * (lender_policy.scoring.weights.get(criterion_type, 10) / 100)

        # Check equipment term matrix if applicable
        if context.equipment_category in lender_policy.equipment_matrices:
            matrix_result = self._evaluate_equipment_matrix(
                context,
                lender_policy.equipment_matrices[context.equipment_category]
            )
            criteria_results["equipment_term"] = matrix_result.to_dict()

            if not matrix_result.passed:
                is_eligible = False
                rejection_reasons.append(matrix_result.message)

        return ProgramEvaluationResult(
            program_id=program.id,
            is_eligible=is_eligible,
            fit_score=int(total_score) if is_eligible else 0,
            criteria_results=criteria_results,
            rejection_reasons=rejection_reasons
        )
```

### Individual Rule Implementations

```python
@rule_registry.register("credit_score")
class CreditScoreRule(Rule):
    """Evaluates personal credit score requirements."""

    def evaluate(self, context: EvaluationContext, criteria: dict) -> RuleResult:
        score_type = criteria.get("type", "fico")
        min_score = criteria.get("min", 0)

        # Get the appropriate score
        score_map = {
            "fico": context.fico_score,
            "transunion": context.transunion_score,
            "experian": context.experian_score,
            "equifax": context.equifax_score,
        }

        actual_score = score_map.get(score_type)

        if actual_score is None:
            return RuleResult(
                passed=False,
                rule_name=f"Minimum {score_type.title()} Score",
                required_value=str(min_score),
                actual_value="Not provided",
                message=f"{score_type.title()} score not provided",
                score=0
            )

        if actual_score >= min_score:
            # Calculate score bonus for exceeding minimum
            excess = actual_score - min_score
            bonus = min(30, excess * 0.3)  # Up to 30 bonus points

            return RuleResult(
                passed=True,
                rule_name=f"Minimum {score_type.title()} Score",
                required_value=str(min_score),
                actual_value=str(actual_score),
                message=f"{score_type.title()} score {actual_score} meets minimum {min_score}",
                score=70 + bonus
            )
        else:
            return RuleResult(
                passed=False,
                rule_name=f"Minimum {score_type.title()} Score",
                required_value=str(min_score),
                actual_value=str(actual_score),
                message=f"{score_type.title()} score {actual_score} below minimum {min_score}",
                score=0
            )


@rule_registry.register("business")
class BusinessRequirementsRule(Rule):
    """Evaluates business requirements (TIB, homeowner, CDL, etc.)."""

    def evaluate(self, context: EvaluationContext, criteria: dict) -> RuleResult:
        failed_checks = []
        passed_checks = []
        total_score = 0
        max_possible = 0

        # Time in business
        if "min_time_in_business_years" in criteria:
            min_tib = criteria["min_time_in_business_years"]
            max_possible += 25

            if context.years_in_business >= min_tib:
                bonus = min(25, (context.years_in_business - min_tib) * 5)
                total_score += bonus
                passed_checks.append(f"Time in business {context.years_in_business} years meets minimum {min_tib} years")
            else:
                failed_checks.append({
                    "check": "Time in Business",
                    "required": f"{min_tib} years",
                    "actual": f"{context.years_in_business} years",
                    "message": f"Time in business {context.years_in_business} years below minimum {min_tib} years"
                })

        # Homeowner requirement
        if criteria.get("requires_homeowner"):
            max_possible += 15
            if context.is_homeowner:
                total_score += 15
                passed_checks.append("Homeowner requirement met")
            else:
                failed_checks.append({
                    "check": "Homeownership",
                    "required": "Must be homeowner",
                    "actual": "Not a homeowner",
                    "message": "Applicant is not a homeowner (required)"
                })

        # CDL requirement (conditional for trucking)
        cdl_required = criteria.get("requires_cdl")
        if cdl_required == "conditional" and context.equipment_category in ["class_8_truck", "trailer", "semi"]:
            cdl_required = True

        if cdl_required is True:
            max_possible += 10
            if context.has_cdl:
                total_score += 10
                passed_checks.append("CDL requirement met")
            else:
                failed_checks.append({
                    "check": "CDL License",
                    "required": "Must have CDL",
                    "actual": "No CDL",
                    "message": "CDL license required but not held"
                })

        # Minimum CDL years
        if "min_cdl_years" in criteria:
            min_cdl_years = criteria["min_cdl_years"]
            max_possible += 15

            if context.cdl_years and context.cdl_years >= min_cdl_years:
                total_score += 15
                passed_checks.append(f"CDL experience {context.cdl_years} years meets minimum {min_cdl_years} years")
            else:
                actual = f"{context.cdl_years} years" if context.cdl_years else "No CDL"
                failed_checks.append({
                    "check": "CDL Experience",
                    "required": f"{min_cdl_years} years",
                    "actual": actual,
                    "message": f"CDL experience {actual} below minimum {min_cdl_years} years"
                })

        # Industry experience
        if "min_industry_experience_years" in criteria:
            min_exp = criteria["min_industry_experience_years"]
            max_possible += 15

            if context.industry_experience_years and context.industry_experience_years >= min_exp:
                total_score += 15
                passed_checks.append(f"Industry experience {context.industry_experience_years} years meets minimum {min_exp} years")
            else:
                actual = f"{context.industry_experience_years} years" if context.industry_experience_years else "Not provided"
                failed_checks.append({
                    "check": "Industry Experience",
                    "required": f"{min_exp} years",
                    "actual": actual,
                    "message": f"Industry experience {actual} below minimum {min_exp} years"
                })

        if failed_checks:
            return RuleResult(
                passed=False,
                rule_name="Business Requirements",
                required_value="; ".join([f["required"] for f in failed_checks]),
                actual_value="; ".join([f["actual"] for f in failed_checks]),
                message=failed_checks[0]["message"],  # Primary rejection reason
                score=0,
                details={"failed_checks": failed_checks, "passed_checks": passed_checks}
            )

        normalized_score = (total_score / max_possible * 100) if max_possible > 0 else 100

        return RuleResult(
            passed=True,
            rule_name="Business Requirements",
            required_value="All met",
            actual_value="All met",
            message="All business requirements satisfied",
            score=normalized_score,
            details={"passed_checks": passed_checks}
        )


@rule_registry.register("credit_history")
class CreditHistoryRule(Rule):
    """Evaluates credit history (bankruptcy, judgements, etc.)."""

    def evaluate(self, context: EvaluationContext, criteria: dict) -> RuleResult:
        failed_checks = []

        # Bankruptcy check
        if context.has_bankruptcy:
            min_discharge_years = criteria.get("bankruptcy_min_discharge_years", 0)

            if context.bankruptcy_discharge_years is None:
                failed_checks.append({
                    "check": "Bankruptcy",
                    "required": "No active bankruptcy",
                    "actual": "Active/undischarged bankruptcy",
                    "message": "Active bankruptcy not allowed"
                })
            elif context.bankruptcy_discharge_years < min_discharge_years:
                failed_checks.append({
                    "check": "Bankruptcy Discharge Period",
                    "required": f"Discharged {min_discharge_years}+ years ago",
                    "actual": f"Discharged {context.bankruptcy_discharge_years:.1f} years ago",
                    "message": f"Bankruptcy discharged {context.bankruptcy_discharge_years:.1f} years ago, minimum {min_discharge_years} years required"
                })

        # Open judgements
        max_judgements = criteria.get("max_open_judgements", 999)
        if context.has_open_judgements and max_judgements == 0:
            failed_checks.append({
                "check": "Open Judgements",
                "required": "No open judgements",
                "actual": f"Has open judgements (${context.judgement_amount:,})" if context.judgement_amount else "Has open judgements",
                "message": "Open judgements not allowed"
            })

        # Tax liens
        max_liens = criteria.get("max_tax_liens", 999)
        if context.has_tax_liens and max_liens == 0:
            failed_checks.append({
                "check": "Tax Liens",
                "required": "No tax liens",
                "actual": f"Has tax liens (${context.tax_lien_amount:,})" if context.tax_lien_amount else "Has tax liens",
                "message": "Tax liens not allowed"
            })

        # Foreclosure
        if context.has_foreclosure and not criteria.get("allows_foreclosure", True):
            failed_checks.append({
                "check": "Foreclosure",
                "required": "No foreclosure history",
                "actual": "Has foreclosure",
                "message": "Foreclosure history not allowed"
            })

        # Repossession
        if context.has_repossession and not criteria.get("allows_repossession", True):
            failed_checks.append({
                "check": "Repossession",
                "required": "No repossession history",
                "actual": "Has repossession",
                "message": "Repossession history not allowed"
            })

        if failed_checks:
            return RuleResult(
                passed=False,
                rule_name="Credit History",
                required_value=failed_checks[0]["required"],
                actual_value=failed_checks[0]["actual"],
                message=failed_checks[0]["message"],
                score=0,
                details={"failed_checks": failed_checks}
            )

        # Score based on clean credit history
        score = 100
        if context.has_bankruptcy and context.bankruptcy_discharge_years:
            # Reduce score if bankruptcy, even if meets minimum
            score -= max(0, 30 - context.bankruptcy_discharge_years * 3)

        return RuleResult(
            passed=True,
            rule_name="Credit History",
            required_value="Clean history",
            actual_value="Acceptable",
            message="Credit history meets requirements",
            score=max(60, score)
        )
```

---

## User Interface

### Pages and Components

```
frontend/src/
├── pages/
│   ├── HomePage.tsx                    # Landing page
│   ├── ApplicationPage.tsx             # New application form
│   ├── ApplicationDetailPage.tsx       # View submitted application
│   ├── ResultsPage.tsx                 # Matching results display
│   └── admin/
│       ├── LenderListPage.tsx          # View all lender policies
│       ├── LenderDetailPage.tsx        # View/edit single lender
│       └── LenderCreatePage.tsx        # Add new lender
│
├── components/
│   ├── application/
│   │   ├── ApplicationForm.tsx         # Main form container
│   │   ├── ApplicantSection.tsx        # Personal/credit info
│   │   ├── BusinessSection.tsx         # Business details
│   │   ├── EquipmentSection.tsx        # Equipment info
│   │   ├── LoanRequestSection.tsx      # Loan amount/term
│   │   └── CreditHistorySection.tsx    # Bankruptcy, liens, etc.
│   │
│   ├── results/
│   │   ├── MatchingResults.tsx         # Results container
│   │   ├── LenderCard.tsx              # Single lender result
│   │   ├── ScoreGauge.tsx              # Visual score display
│   │   ├── CriteriaBreakdown.tsx       # Detailed pass/fail list
│   │   └── RejectionReasons.tsx        # Why not eligible
│   │
│   └── admin/
│       ├── LenderPolicyForm.tsx        # Edit lender form
│       ├── ProgramEditor.tsx           # Edit programs/tiers
│       ├── CriteriaEditor.tsx          # Edit criteria
│       └── EquipmentMatrixEditor.tsx   # Edit term matrices
│
└── types/
    ├── application.ts
    ├── matching.ts
    └── lender.ts
```

### Application Form

Multi-step form collecting all required information:

**Step 1: Applicant Information**
- FICO Score (required)
- TransUnion Score (optional)
- PayNet Score (optional)
- Is Homeowner (yes/no)
- Is US Citizen (yes/no)

**Step 2: Business Information**
- Business Legal Name
- State (dropdown)
- Industry (dropdown with NAICS codes)
- Years in Business
- Annual Revenue (optional)
- Fleet Size (for trucking)

**Step 3: Equipment Details**
- Equipment Category (dropdown)
- Equipment Type
- Year
- Mileage (if applicable)
- Hours (if applicable)
- Condition (new/used)

**Step 4: Credit History**
- Bankruptcy (yes/no, if yes: chapter, discharge date)
- Open Judgements (yes/no, amount)
- Foreclosure (yes/no)
- Repossession (yes/no)
- Tax Liens (yes/no, amount)

**Step 5: Loan Request**
- Loan Amount
- Requested Term (optional)
- Transaction Type (purchase/refinance/sale-leaseback)
- Is Private Party Sale (yes/no)
- Down Payment % (optional)

### Results Display

```tsx
// MatchingResults.tsx
const MatchingResults: React.FC<{ applicationId: string }> = ({ applicationId }) => {
  const { data: results, isLoading } = useQuery(
    ['matchResults', applicationId],
    () => fetchMatchResults(applicationId)
  );

  if (isLoading) return <LoadingSpinner />;

  const eligibleLenders = results.matches.filter(m => m.is_eligible);
  const ineligibleLenders = results.matches.filter(m => !m.is_eligible);

  return (
    <div className="results-container">
      {/* Summary */}
      <div className="results-summary">
        <h2>Matching Results</h2>
        <p>{eligibleLenders.length} of {results.matches.length} lenders matched</p>

        {results.best_match && (
          <div className="best-match-highlight">
            <span>Best Match:</span>
            <strong>{results.best_match.lender_name}</strong>
            <ScoreGauge score={results.best_match.fit_score} />
          </div>
        )}
      </div>

      {/* Eligible Lenders */}
      <section className="eligible-lenders">
        <h3>Eligible Lenders</h3>
        {eligibleLenders.map(match => (
          <LenderCard
            key={match.lender_id}
            match={match}
            isExpanded={match.rank === 1}
          />
        ))}
      </section>

      {/* Ineligible Lenders (Collapsed) */}
      <section className="ineligible-lenders">
        <Collapsible title={`Ineligible Lenders (${ineligibleLenders.length})`}>
          {ineligibleLenders.map(match => (
            <LenderCard
              key={match.lender_id}
              match={match}
              showRejectionReasons
            />
          ))}
        </Collapsible>
      </section>
    </div>
  );
};
```

```tsx
// CriteriaBreakdown.tsx - Shows detailed pass/fail for each criterion
const CriteriaBreakdown: React.FC<{ criteria: CriteriaResults }> = ({ criteria }) => {
  return (
    <div className="criteria-breakdown">
      <h4>Criteria Evaluation</h4>
      <table>
        <thead>
          <tr>
            <th>Criterion</th>
            <th>Required</th>
            <th>Actual</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(criteria).map(([key, result]) => (
            <tr key={key} className={result.passed ? 'passed' : 'failed'}>
              <td>{result.rule_name}</td>
              <td>{result.required_value}</td>
              <td>{result.actual_value}</td>
              <td>
                {result.passed ? (
                  <CheckIcon className="text-green-500" />
                ) : (
                  <XIcon className="text-red-500" />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Detailed message for failed criteria */}
      {Object.entries(criteria)
        .filter(([_, r]) => !r.passed)
        .map(([key, result]) => (
          <div key={key} className="failure-detail">
            <strong>{result.rule_name}:</strong> {result.message}
          </div>
        ))}
    </div>
  );
};
```

### Lender Policy Management

```tsx
// LenderListPage.tsx
const LenderListPage: React.FC = () => {
  const { data: lenders } = useQuery('lenders', fetchLenders);

  return (
    <div className="lender-list-page">
      <header>
        <h1>Lender Policies</h1>
        <Button onClick={() => navigate('/admin/lenders/new')}>
          Add New Lender
        </Button>
      </header>

      <table className="lenders-table">
        <thead>
          <tr>
            <th>Lender</th>
            <th>Programs</th>
            <th>Status</th>
            <th>Last Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {lenders?.map(lender => (
            <tr key={lender.id}>
              <td>
                <Link to={`/admin/lenders/${lender.id}`}>
                  {lender.name}
                </Link>
              </td>
              <td>{lender.programs_count}</td>
              <td>
                <StatusBadge active={lender.is_active} />
              </td>
              <td>{formatDate(lender.policy_last_updated)}</td>
              <td>
                <Button variant="link" onClick={() => navigate(`/admin/lenders/${lender.id}/edit`)}>
                  Edit
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

```tsx
// LenderDetailPage.tsx - View/Edit single lender policy
const LenderDetailPage: React.FC = () => {
  const { lenderId } = useParams();
  const { data: lender } = useQuery(['lender', lenderId], () => fetchLender(lenderId));
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="lender-detail-page">
      <header>
        <h1>{lender?.name}</h1>
        <div>
          <StatusBadge active={lender?.is_active} />
          <Button onClick={() => setIsEditing(!isEditing)}>
            {isEditing ? 'Cancel' : 'Edit Policy'}
          </Button>
        </div>
      </header>

      {/* Contact Info */}
      <section className="contact-info">
        <h2>Contact</h2>
        <p>{lender?.contact_name}</p>
        <p>{lender?.contact_email}</p>
        <p>{lender?.contact_phone}</p>
      </section>

      {/* Programs */}
      <section className="programs">
        <h2>Programs</h2>
        {lender?.programs.map(program => (
          <ProgramCard
            key={program.id}
            program={program}
            isEditing={isEditing}
          />
        ))}
        {isEditing && (
          <Button variant="outline" onClick={addProgram}>
            + Add Program
          </Button>
        )}
      </section>

      {/* Restrictions */}
      <section className="restrictions">
        <h2>Restrictions</h2>
        <RestrictionsEditor
          restrictions={lender?.restrictions}
          isEditing={isEditing}
        />
      </section>

      {/* Equipment Matrices */}
      <section className="equipment-matrices">
        <h2>Equipment Term Matrices</h2>
        <EquipmentMatrixEditor
          matrices={lender?.equipment_matrices}
          isEditing={isEditing}
        />
      </section>

      {isEditing && (
        <div className="save-actions">
          <Button variant="primary" onClick={savePolicy}>
            Save Changes
          </Button>
        </div>
      )}
    </div>
  );
};
```

---

## API Endpoints

### Application Endpoints

```
POST   /api/v1/applications                    # Submit new application
GET    /api/v1/applications                    # List applications (paginated)
GET    /api/v1/applications/{id}               # Get application details
GET    /api/v1/applications/{id}/results       # Get matching results
GET    /api/v1/applications/{id}/status        # Get processing status
```

### Lender Endpoints

```
GET    /api/v1/lenders                         # List all lenders
GET    /api/v1/lenders/{id}                    # Get lender details with policy
POST   /api/v1/lenders                         # Create new lender
PUT    /api/v1/lenders/{id}                    # Update lender
PATCH  /api/v1/lenders/{id}/status             # Toggle active/inactive
DELETE /api/v1/lenders/{id}                    # Delete lender (soft delete)
```

### Admin/Onboarding Endpoints

```
POST   /api/v1/onboarding/upload               # Upload PDF for AI parsing
GET    /api/v1/onboarding/{id}/status          # Check parsing status
GET    /api/v1/onboarding/{id}/draft           # Get generated YAML draft
POST   /api/v1/onboarding/{id}/approve         # Approve and activate
```

---

## File Structure

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── business.py              # Business model
│   │   ├── guarantor.py             # PersonalGuarantor model
│   │   ├── business_credit.py       # BusinessCredit model
│   │   ├── application.py           # LoanApplication model
│   │   ├── lender.py                # Lender model (DB metadata)
│   │   └── match_result.py          # MatchResult model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── application.py           # Input/output schemas
│   │   ├── matching.py              # Result schemas
│   │   └── lender.py                # Lender schemas
│   │
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── schema.py                # Pydantic models for YAML validation
│   │   ├── loader.py                # Loads & validates YAML files
│   │   └── lenders/
│   │       ├── _template.yaml
│   │       ├── citizens_bank.yaml
│   │       ├── advantage_plus.yaml
│   │       ├── stearns_bank.yaml
│   │       ├── falcon_equipment.yaml
│   │       └── apex_commercial.yaml
│   │
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── base.py                  # Rule, RuleResult, EvaluationContext
│   │   ├── engine.py                # MatchingEngine
│   │   ├── registry.py              # RuleRegistry
│   │   └── criteria/
│   │       ├── __init__.py
│   │       ├── credit_score.py
│   │       ├── business.py
│   │       ├── equipment.py
│   │       ├── geographic.py
│   │       ├── industry.py
│   │       ├── credit_history.py
│   │       ├── transaction.py
│   │       └── loan_amount.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── application_service.py   # Application CRUD
│   │   ├── matching_service.py      # Matching orchestration
│   │   └── lender_service.py        # Lender CRUD
│   │
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── evaluation.py            # Hatchet workflow
│   │
│   └── api/
│       ├── __init__.py
│       ├── deps.py                  # Dependencies
│       └── routes/
│           ├── __init__.py
│           ├── applications.py
│           ├── lenders.py
│           └── onboarding.py

frontend/
├── src/
│   ├── api/
│   │   ├── client.ts
│   │   ├── applications.ts
│   │   ├── lenders.ts
│   │   └── types.ts
│   │
│   ├── components/
│   │   ├── ui/                      # Existing components
│   │   ├── application/
│   │   ├── results/
│   │   └── admin/
│   │
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── ApplicationPage.tsx
│   │   ├── ApplicationDetailPage.tsx
│   │   ├── ResultsPage.tsx
│   │   └── admin/
│   │
│   └── types/
│       ├── application.ts
│       ├── matching.ts
│       └── lender.ts
```

---

## Implementation Phases

### Phase 1: Data Models & Database
- [ ] Create all SQLAlchemy models
- [ ] Set up Alembic migrations
- [ ] Create Pydantic schemas for API

### Phase 2: Core Rule Engine
- [ ] Implement base classes (Rule, RuleResult, EvaluationContext)
- [ ] Create RuleRegistry
- [ ] Implement individual rule types
- [ ] Create MatchingEngine

### Phase 3: Policy System
- [ ] Define YAML schema with Pydantic validation
- [ ] Implement PolicyLoader
- [ ] Create YAML files for 5 lenders
- [ ] Create Lender database model for UI management

### Phase 4: Hatchet Workflow
- [ ] Set up Hatchet integration
- [ ] Implement ApplicationEvaluationWorkflow
- [ ] Add parallel lender evaluation
- [ ] Add retry logic and error handling

### Phase 5: API Endpoints
- [ ] Application CRUD endpoints
- [ ] Matching results endpoints
- [ ] Lender management endpoints

### Phase 6: Frontend - Application Form
- [ ] Multi-step form with validation
- [ ] All input sections
- [ ] Form submission

### Phase 7: Frontend - Results Display
- [ ] Matching results page
- [ ] Lender cards with scores
- [ ] Criteria breakdown component
- [ ] Rejection reasons display

### Phase 8: Frontend - Policy Management
- [ ] Lender list page
- [ ] Lender detail/edit page
- [ ] Add new lender page

### Phase 9: Testing & Refinement
- [ ] Unit tests for rules
- [ ] Integration tests for matching
- [ ] E2E tests for UI
- [ ] Performance optimization

---

## Lender Guidelines (Source PDFs)

| File | Lender |
|------|--------|
| `data/2025 Program Guidelines UPDATED.pdf` | Citizens Bank |
| `data/Advantage++Broker+2025.pdf` | Advantage+ Financing |
| `data/112025 Rates - STANDARD.pdf` | Stearns Bank |
| `data/EF Credit Box 4.14.2025.pdf` | Falcon Equipment Finance |
| `data/Apex EF Broker Guidelines_082725.pdf` | Apex Commercial Capital |

---

## Key Design Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Policy storage | YAML files + DB metadata | YAML for rules (human-readable, git-versioned), DB for UI management |
| Workflow engine | Hatchet | Built-in parallelization, retry logic, observability |
| Rule engine | Registry pattern | Extensible, testable, easy to add new rule types |
| Scoring | 0-100 weighted | Allows ranking among eligible lenders |
| Results persistence | Full detail in JSON | Audit trail, detailed UI display, no re-computation needed |
| Frontend | React + TypeScript | Type safety, component reuse, modern tooling |

---

## Adding New Lenders

### Via UI
1. Go to Admin > Lenders > Add New
2. Fill in lender info and contact
3. Define programs with criteria
4. Set restrictions and equipment matrices
5. Save and activate

### Via YAML
1. Copy `policies/lenders/_template.yaml` to `new_lender.yaml`
2. Fill in all criteria from PDF/guidelines
3. Validate: `python -m backend.app.policies.validate new_lender`
4. Add DB record for UI display
5. Commit to git

### Via AI-Assisted PDF Upload
1. Upload PDF to `/api/v1/onboarding/upload`
2. Wait for AI parsing (Hatchet workflow)
3. Review generated YAML draft
4. Make corrections if needed
5. Approve to activate

---

## Adding New Rule Types

1. Create class in `rules/criteria/`:

```python
@rule_registry.register("new_criterion")
class NewCriterionRule(Rule):
    def evaluate(self, context: EvaluationContext, criteria: dict) -> RuleResult:
        # Implementation
        pass
```

2. Update `policies/schema.py` to validate new criterion in YAML
3. Use in lender YAML files
4. Add to UI criteria editor if needed
