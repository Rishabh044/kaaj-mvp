# Lender Matching Platform - PR Release Plan

This document outlines the phased PR approach for building the Lender Matching Platform MVP. Each PR is designed to be independently reviewable, testable, and mergeable while building towards the complete system.

---

## PR Overview

| PR | Title | Dependencies | Estimated Files |
|----|-------|--------------|-----------------|
| PR-1 | Project Setup & Infrastructure | None | ~25 |
| PR-2 | Database Models & Schemas | PR-1 | ~20 |
| PR-3 | Rule Engine Foundation | PR-1 | ~15 |
| PR-4 | Policy System & Lender Configurations | PR-3 | ~12 |
| PR-5 | Matching Engine & Service | PR-2, PR-3, PR-4 | ~8 |
| PR-6 | Hatchet Workflow Integration | PR-2, PR-5 | ~6 |
| PR-7 | Backend API Endpoints | PR-2, PR-5, PR-6 | ~12 |
| PR-8 | Frontend Application Form | PR-7 | ~18 |
| PR-9 | Frontend Results & Policy Management | PR-7, PR-8 | ~15 |
| PR-10 | E2E Testing & Polish | All | ~10 |

---

## PR-1: Project Setup & Infrastructure

**Status:** COMPLETED

### Why We're Doing This
Establish the foundational project structure, tooling, and CI/CD pipeline that all subsequent development will build upon. A solid foundation ensures consistent development practices, automated quality checks, and containerized deployment.

### What Was Done
- Backend: FastAPI application structure with async SQLAlchemy, Alembic migrations, health endpoints
- Frontend: React + TypeScript with Vite, TailwindCSS, component library foundation
- Infrastructure: Docker configurations, GitHub Actions CI pipeline
- Testing: pytest setup for backend, Vitest for frontend

### Files Changed
```
backend/
├── app/main.py
├── app/core/config.py
├── app/core/database.py
├── alembic/
├── requirements.txt
├── Dockerfile
frontend/
├── package.json
├── vite.config.ts
├── src/App.tsx
├── src/components/ui/
.github/workflows/ci.yml
docker-compose.yml
.env.example
```

---

## PR-2: Database Models & Schemas

### Why We're Doing This
Define the complete data model for the loan application system. These models represent the core domain entities: businesses applying for loans, personal guarantors with their credit profiles, loan applications with equipment details, and match results. Proper normalization ensures data integrity and enables efficient querying.

### How It Will Be Done

#### Step 1: Create SQLAlchemy Base Model
Extend the existing `Base` class with common fields and utilities.

```python
# backend/app/models/base.py
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

#### Step 2: Implement Domain Models
Create each model in its own file following the schema from IMPLEMENTATION_PLAN.md:
- `business.py` - Business entity with industry, location, metrics
- `guarantor.py` - PersonalGuarantor with credit scores and history
- `business_credit.py` - BusinessCredit with PayNet, trade lines
- `application.py` - LoanApplication with equipment and loan details
- `lender.py` - Lender with policy file reference
- `match_result.py` - MatchResult with JSON criteria details

#### Step 3: Create Alembic Migrations
Generate migrations for all models with proper foreign key constraints.

#### Step 4: Implement Pydantic Schemas
Create request/response schemas for API serialization.

### Files to Create/Modify

```
backend/app/models/
├── __init__.py              # Export all models
├── base.py                  # TimestampMixin, UUIDMixin
├── business.py              # Business model
├── guarantor.py             # PersonalGuarantor model
├── business_credit.py       # BusinessCredit model
├── application.py           # LoanApplication model
├── lender.py                # Lender model
└── match_result.py          # MatchResult model

backend/app/schemas/
├── __init__.py              # Export all schemas
├── common.py                # Shared schema components
├── business.py              # Business schemas
├── guarantor.py             # Guarantor schemas
├── application.py           # Application input/output schemas
├── lender.py                # Lender schemas
└── matching.py              # Match result schemas

backend/alembic/versions/
└── 002_create_domain_models.py
```

### Unit Tests

```
backend/tests/unit/models/
├── __init__.py
├── test_business.py
│   ├── test_business_creation
│   ├── test_business_years_in_business_validation
│   ├── test_business_state_code_validation
│   └── test_business_relationships
├── test_guarantor.py
│   ├── test_guarantor_creation
│   ├── test_credit_score_range_validation
│   ├── test_bankruptcy_date_logic
│   └── test_credit_history_flags
├── test_business_credit.py
│   ├── test_business_credit_creation
│   ├── test_paynet_score_range
│   └── test_business_relationship
├── test_application.py
│   ├── test_application_creation
│   ├── test_application_number_uniqueness
│   ├── test_equipment_age_calculation
│   ├── test_loan_amount_validation
│   └── test_status_transitions
├── test_lender.py
│   ├── test_lender_creation
│   ├── test_policy_file_reference
│   └── test_active_status_toggle
└── test_match_result.py
    ├── test_match_result_creation
    ├── test_criteria_results_json_structure
    ├── test_rejection_reasons_list
    └── test_ranking_logic

backend/tests/unit/schemas/
├── __init__.py
├── test_application_schemas.py
│   ├── test_loan_application_input_validation
│   ├── test_required_fields_validation
│   ├── test_equipment_category_enum
│   └── test_transaction_type_enum
├── test_guarantor_schemas.py
│   ├── test_credit_score_bounds
│   └── test_bankruptcy_conditional_fields
└── test_matching_schemas.py
    ├── test_match_result_response_structure
    └── test_criteria_result_schema
```

### Independence
This PR can be developed independently after PR-1. It has no dependencies on the rule engine or matching logic. Models can be tested in isolation using an in-memory SQLite database.

---

## PR-3: Rule Engine Foundation

### Why We're Doing This
The rule engine is the core intelligence of the matching system. It provides a flexible, extensible framework for evaluating loan applications against lender criteria. Using the Specification pattern with a registry allows new rules to be added without modifying existing code, making the system maintainable as lender requirements evolve.

### How It Will Be Done

#### Step 1: Define Base Abstractions
Create the core types that all rules will use.

```python
# backend/app/rules/base.py
@dataclass
class EvaluationContext:
    """Contains all data needed for rule evaluation."""
    # Credit scores, business info, equipment, loan request, credit history
    ...

@dataclass
class RuleResult:
    """Output of a rule evaluation."""
    passed: bool
    rule_name: str
    required_value: str
    actual_value: str
    message: str
    score: float  # 0-100
    details: Optional[dict] = None

class Rule(ABC):
    """Abstract base class for all rules."""
    @property
    @abstractmethod
    def rule_type(self) -> str: ...

    @abstractmethod
    def evaluate(self, context: EvaluationContext, criteria: dict) -> RuleResult: ...
```

#### Step 2: Implement Rule Registry
Create a decorator-based registry for automatic rule discovery.

```python
# backend/app/rules/registry.py
class RuleRegistry:
    _rules: dict[str, type[Rule]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(rule_class: type[Rule]):
            cls._rules[name] = rule_class
            return rule_class
        return decorator

    @classmethod
    def get_rule(cls, name: str) -> Rule:
        return cls._rules[name]()
```

#### Step 3: Implement Individual Rules
Each rule evaluates one category of criteria.

| Rule File | Rules Implemented |
|-----------|-------------------|
| `credit_score.py` | FICORule, TransUnionRule, PayNetRule, ExperianRule, EquifaxRule |
| `business.py` | TimeInBusinessRule, HomeownerRule, CDLRule, FleetSizeRule, IndustryExperienceRule |
| `equipment.py` | EquipmentAgeRule, MileageRule, HoursRule, TermMatrixRule |
| `geographic.py` | StateRestrictionRule |
| `industry.py` | IndustryExclusionRule |
| `credit_history.py` | BankruptcyRule, JudgementRule, ForeclosureRule, RepossessionRule, TaxLienRule |
| `transaction.py` | TransactionTypeRule, PrivatePartyRule |
| `loan_amount.py` | MinAmountRule, MaxAmountRule |

### Files to Create/Modify

```
backend/app/rules/
├── __init__.py              # Export Rule, RuleResult, EvaluationContext, registry
├── base.py                  # EvaluationContext, RuleResult, Rule ABC
├── registry.py              # RuleRegistry with decorator
└── criteria/
    ├── __init__.py          # Import all rules to trigger registration
    ├── credit_score.py      # Credit score rules
    ├── business.py          # Business requirement rules
    ├── equipment.py         # Equipment rules including term matrix
    ├── geographic.py        # State restriction rule
    ├── industry.py          # Industry exclusion rule
    ├── credit_history.py    # Credit history rules
    ├── transaction.py       # Transaction type rules
    └── loan_amount.py       # Loan amount rules
```

### Unit Tests

```
backend/tests/unit/rules/
├── __init__.py
├── test_base.py
│   ├── test_evaluation_context_creation
│   ├── test_evaluation_context_optional_fields
│   ├── test_rule_result_passed_property
│   └── test_rule_result_score_bounds
├── test_registry.py
│   ├── test_register_decorator
│   ├── test_get_registered_rule
│   ├── test_get_unregistered_rule_raises
│   └── test_list_all_rules
├── test_credit_score.py
│   ├── test_fico_score_passes_when_meets_minimum
│   ├── test_fico_score_fails_when_below_minimum
│   ├── test_fico_score_not_provided
│   ├── test_fico_score_bonus_calculation
│   ├── test_transunion_score_evaluation
│   ├── test_paynet_score_evaluation
│   └── test_score_type_selection
├── test_business.py
│   ├── test_time_in_business_passes
│   ├── test_time_in_business_fails
│   ├── test_homeowner_required_passes
│   ├── test_homeowner_required_fails
│   ├── test_cdl_conditional_trucking
│   ├── test_cdl_not_required_non_trucking
│   ├── test_cdl_years_minimum
│   ├── test_industry_experience_minimum
│   ├── test_fleet_size_minimum
│   └── test_multiple_requirements_all_must_pass
├── test_equipment.py
│   ├── test_equipment_age_within_limit
│   ├── test_equipment_age_exceeds_limit
│   ├── test_mileage_within_limit
│   ├── test_mileage_exceeds_limit
│   ├── test_hours_within_limit
│   ├── test_term_matrix_lookup_by_mileage
│   ├── test_term_matrix_lookup_by_age
│   ├── test_term_matrix_not_desired
│   └── test_term_matrix_missing_category
├── test_geographic.py
│   ├── test_state_allowed
│   ├── test_state_excluded
│   ├── test_empty_exclusion_list
│   └── test_case_insensitive_state
├── test_industry.py
│   ├── test_industry_allowed
│   ├── test_industry_excluded
│   └── test_industry_code_matching
├── test_credit_history.py
│   ├── test_no_bankruptcy_passes
│   ├── test_bankruptcy_within_discharge_period
│   ├── test_bankruptcy_outside_discharge_period
│   ├── test_active_bankruptcy_fails
│   ├── test_open_judgements_not_allowed
│   ├── test_open_judgements_allowed_with_limit
│   ├── test_foreclosure_check
│   ├── test_repossession_check
│   ├── test_tax_liens_check
│   └── test_multiple_credit_issues
├── test_transaction.py
│   ├── test_purchase_allowed
│   ├── test_refinance_not_allowed
│   ├── test_sale_leaseback_not_allowed
│   └── test_private_party_restriction
└── test_loan_amount.py
    ├── test_amount_within_range
    ├── test_amount_below_minimum
    ├── test_amount_above_maximum
    └── test_no_limits_always_passes
```

### Independence
This PR depends only on PR-1 for the base project structure. It does not require the database models - `EvaluationContext` is a standalone dataclass. Rules can be fully tested in isolation with mock contexts.

---

## PR-4: Policy System & Lender Configurations

### Why We're Doing This
Lender policies define the criteria each lender uses to evaluate applications. Storing policies as YAML files enables:
- Human-readable format with comments explaining business logic
- Version control for audit trails
- Easy editing without code changes
- No database migrations when adding lenders

### How It Will Be Done

#### Step 1: Define Policy Schema with Pydantic
Create Pydantic models that validate YAML structure.

```python
# backend/app/policies/schema.py
class CreditScoreCriteria(BaseModel):
    type: Literal["fico", "transunion", "paynet", "experian", "equifax"]
    min: int = Field(ge=300, le=850)

class BusinessCriteria(BaseModel):
    min_time_in_business_years: Optional[float] = None
    requires_homeowner: Optional[bool] = None
    requires_cdl: Optional[Union[bool, Literal["conditional"]]] = None
    # ... more fields

class ProgramCriteria(BaseModel):
    credit_score: Optional[CreditScoreCriteria] = None
    business: Optional[BusinessCriteria] = None
    credit_history: Optional[CreditHistoryCriteria] = None
    # ... more criteria types

class LenderProgram(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_app_only: bool = False
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    criteria: ProgramCriteria

class LenderPolicy(BaseModel):
    id: str
    name: str
    version: int
    programs: list[LenderProgram]
    equipment_matrices: Optional[dict] = None
    restrictions: Optional[Restrictions] = None
    scoring: Optional[ScoringConfig] = None
```

#### Step 2: Implement Policy Loader
Load, validate, and cache YAML policies.

```python
# backend/app/policies/loader.py
class PolicyLoader:
    def __init__(self, policies_dir: Path):
        self.policies_dir = policies_dir
        self._cache: dict[str, LenderPolicy] = {}

    def load_policy(self, lender_id: str) -> LenderPolicy:
        """Load and validate a single lender policy."""
        ...

    def get_active_lenders(self) -> list[LenderPolicy]:
        """Load all active lender policies."""
        ...

    def reload(self):
        """Clear cache and reload all policies."""
        ...
```

#### Step 3: Create Lender YAML Files
Parse the 5 PDF guidelines and create corresponding YAML files:

| PDF | YAML Output |
|-----|-------------|
| `2025 Program Guidelines UPDATED.pdf` | `citizens_bank.yaml` |
| `Advantage++Broker+2025.pdf` | `advantage_plus.yaml` |
| `112025 Rates - STANDARD.pdf` | `stearns_bank.yaml` |
| `EF Credit Box 4.14.2025.pdf` | `falcon_equipment.yaml` |
| `Apex EF Broker Guidelines_082725.pdf` | `apex_commercial.yaml` |

### Files to Create/Modify

```
backend/app/policies/
├── __init__.py              # Export PolicyLoader, schema classes
├── schema.py                # Pydantic models for YAML validation
├── loader.py                # PolicyLoader class
└── lenders/
    ├── _template.yaml       # Template for new lenders
    ├── citizens_bank.yaml   # Citizens Bank policy
    ├── advantage_plus.yaml  # Advantage+ Financing policy
    ├── stearns_bank.yaml    # Stearns Bank policy
    ├── falcon_equipment.yaml # Falcon Equipment Finance policy
    └── apex_commercial.yaml  # Apex Commercial Capital policy
```

### Unit Tests

```
backend/tests/unit/policies/
├── __init__.py
├── test_schema.py
│   ├── test_credit_score_criteria_validation
│   ├── test_credit_score_invalid_type
│   ├── test_credit_score_out_of_range
│   ├── test_business_criteria_validation
│   ├── test_cdl_conditional_value
│   ├── test_program_criteria_composition
│   ├── test_lender_program_validation
│   ├── test_equipment_matrix_structure
│   ├── test_restrictions_validation
│   └── test_full_lender_policy_validation
├── test_loader.py
│   ├── test_load_single_policy
│   ├── test_load_nonexistent_policy
│   ├── test_load_invalid_yaml_syntax
│   ├── test_load_invalid_schema
│   ├── test_get_active_lenders
│   ├── test_policy_caching
│   ├── test_cache_invalidation
│   └── test_reload_policies
├── test_citizens_bank.py
│   ├── test_citizens_bank_loads_successfully
│   ├── test_citizens_bank_has_three_programs
│   ├── test_citizens_bank_tier1_criteria
│   ├── test_citizens_bank_equipment_matrix
│   └── test_citizens_bank_state_restrictions
├── test_advantage_plus.py
│   ├── test_advantage_plus_loads_successfully
│   ├── test_advantage_plus_non_trucking_only
│   └── test_advantage_plus_credit_history_strict
├── test_stearns_bank.py
│   ├── test_stearns_bank_loads_successfully
│   ├── test_stearns_bank_tiered_programs
│   └── test_stearns_bank_no_paynet_alternative
├── test_falcon_equipment.py
│   ├── test_falcon_loads_successfully
│   ├── test_falcon_trucking_requirements
│   └── test_falcon_fleet_size_requirement
└── test_apex_commercial.py
    ├── test_apex_loads_successfully
    ├── test_apex_tiered_rates
    └── test_apex_medical_program
```

### Independence
This PR depends on PR-3 (rule engine) because policies reference rule types. However, the schema validation and YAML loading can be developed independently. Policy files should be validated against the schema but don't require the actual rule implementations to test loading.

---

## PR-5: Matching Engine & Service

### Why We're Doing This
The matching engine orchestrates the evaluation of a loan application against all lender policies. It determines eligibility, finds the best matching program, calculates fit scores, and provides detailed rejection reasons. This is the core business logic that ties together rules and policies.

### How It Will Be Done

#### Step 1: Create EvaluationContext Builder
Transform database models into the EvaluationContext used by rules.

```python
# backend/app/rules/context_builder.py
def build_evaluation_context(
    application: LoanApplication,
    derived_features: dict
) -> EvaluationContext:
    """Assemble evaluation context from database models."""
    return EvaluationContext(
        fico_score=application.guarantor.fico_score,
        transunion_score=application.guarantor.transunion_score,
        # ... all fields
    )
```

#### Step 2: Implement MatchingEngine
The engine evaluates one lender at a time.

```python
# backend/app/rules/engine.py
class MatchingEngine:
    def __init__(self, rule_registry: RuleRegistry):
        self.registry = rule_registry

    async def evaluate_lender(
        self,
        context: EvaluationContext,
        lender_policy: LenderPolicy
    ) -> LenderMatchResult:
        """Evaluate application against a single lender."""
        # 1. Check hard restrictions (state, industry)
        # 2. Evaluate each program
        # 3. Find best matching program
        # 4. Calculate fit score
        # 5. Compile rejection reasons if ineligible
```

#### Step 3: Create Matching Service
High-level service that coordinates matching across all lenders.

```python
# backend/app/services/matching_service.py
class LenderMatchingService:
    def __init__(self, engine: MatchingEngine, policy_loader: PolicyLoader):
        self.engine = engine
        self.policy_loader = policy_loader

    async def match_application(
        self,
        context: EvaluationContext,
        lender_ids: Optional[list[str]] = None
    ) -> MatchingResult:
        """Evaluate application against all (or specified) lenders."""
        lenders = self.policy_loader.get_active_lenders()

        # Evaluate all lenders (will be parallelized in workflow)
        matches = []
        for lender in lenders:
            result = await self.engine.evaluate_lender(context, lender)
            matches.append(result)

        # Sort by eligibility and score
        matches.sort(key=lambda m: (m.is_eligible, m.fit_score), reverse=True)

        return MatchingResult(
            matches=matches,
            best_match=matches[0] if matches[0].is_eligible else None,
            total_eligible=sum(1 for m in matches if m.is_eligible)
        )
```

### Files to Create/Modify

```
backend/app/rules/
├── context_builder.py       # build_evaluation_context function
└── engine.py                # MatchingEngine class

backend/app/services/
├── __init__.py
└── matching_service.py      # LenderMatchingService class

backend/app/schemas/
└── matching.py              # LenderMatchResult, MatchingResult schemas (extend)
```

### Unit Tests

```
backend/tests/unit/rules/
└── test_context_builder.py
    ├── test_build_context_full_application
    ├── test_build_context_minimal_application
    ├── test_build_context_with_business_credit
    ├── test_build_context_derived_features_override
    └── test_build_context_null_handling

backend/tests/unit/services/
├── __init__.py
└── test_matching_engine.py
    ├── test_evaluate_lender_eligible
    ├── test_evaluate_lender_ineligible_credit_score
    ├── test_evaluate_lender_ineligible_state
    ├── test_evaluate_lender_multiple_programs_best_match
    ├── test_evaluate_lender_fit_score_calculation
    ├── test_evaluate_lender_rejection_reasons
    ├── test_evaluate_lender_equipment_matrix
    └── test_evaluate_lender_program_amount_bounds

backend/tests/integration/
├── __init__.py
└── test_matching_service.py
    ├── test_match_application_all_lenders
    ├── test_match_application_specific_lenders
    ├── test_match_application_ranking_by_score
    ├── test_match_application_no_eligible_lenders
    ├── test_match_application_all_eligible
    ├── test_match_application_ca_applicant_restricted
    ├── test_match_application_startup_business
    ├── test_match_application_high_mileage_truck
    └── test_match_application_bankruptcy_history
```

### Independence
This PR depends on PR-2 (models for context building), PR-3 (rule engine), and PR-4 (policies). However, the engine can be tested with mock policies and contexts, allowing parallel development with policy file creation.

---

## PR-6: Hatchet Workflow Integration

### Why We're Doing This
Hatchet provides workflow orchestration with built-in parallelization, retry logic, and observability. Using Hatchet for application evaluation enables:
- Parallel evaluation across multiple lenders for performance
- Automatic retries on transient failures (DB connections, etc.)
- Workflow status tracking for async operations
- Clear step-by-step execution for debugging

### How It Will Be Done

#### Step 1: Set Up Hatchet Client
Configure Hatchet connection and dependencies.

```python
# backend/app/core/hatchet.py
from hatchet_sdk import Hatchet

hatchet = Hatchet()

def get_hatchet() -> Hatchet:
    return hatchet
```

#### Step 2: Implement Evaluation Workflow
Create the 4-step workflow from IMPLEMENTATION_PLAN.md.

```python
# backend/app/workflows/evaluation.py
@hatchet.workflow(name="application-evaluation", on_events=["application:submitted"])
class ApplicationEvaluationWorkflow:

    @hatchet.step(timeout="30s", retries=3)
    async def validate_application(self, context: Context) -> dict:
        """Validate required fields."""
        ...

    @hatchet.step(timeout="30s", parents=["validate_application"])
    async def derive_features(self, context: Context) -> dict:
        """Compute equipment age, bankruptcy years, etc."""
        ...

    @hatchet.step(timeout="2m", parents=["derive_features"], retries=2)
    async def evaluate_all_lenders(self, context: Context) -> dict:
        """Parallel evaluation using asyncio.gather."""
        ...

    @hatchet.step(timeout="30s", parents=["evaluate_all_lenders"], retries=3)
    async def persist_and_rank_results(self, context: Context) -> dict:
        """Persist to database and compute rankings."""
        ...
```

#### Step 3: Create Workflow Trigger Utility
Helper function to trigger workflow from API.

```python
# backend/app/workflows/triggers.py
async def trigger_evaluation(
    hatchet_client: Hatchet,
    application_id: str
) -> str:
    """Trigger evaluation workflow, return run ID."""
    run = await hatchet_client.admin.run_workflow(
        "application-evaluation",
        input={"application_id": application_id}
    )
    return run.workflow_run_id
```

### Files to Create/Modify

```
backend/app/core/
└── hatchet.py               # Hatchet client setup

backend/app/workflows/
├── __init__.py              # Export workflows
├── evaluation.py            # ApplicationEvaluationWorkflow
└── triggers.py              # Workflow trigger utilities

backend/app/core/config.py   # Add HATCHET_CLIENT_TOKEN setting
```

### Unit Tests

```
backend/tests/unit/workflows/
├── __init__.py
├── test_validate_application.py
│   ├── test_validate_complete_application
│   ├── test_validate_missing_fico_score
│   ├── test_validate_missing_state
│   ├── test_validate_missing_loan_amount
│   ├── test_validate_missing_equipment_category
│   └── test_validate_multiple_errors
├── test_derive_features.py
│   ├── test_derive_equipment_age
│   ├── test_derive_bankruptcy_discharge_years
│   ├── test_derive_is_startup
│   ├── test_derive_is_trucking
│   └── test_derive_skips_on_validation_failure
├── test_evaluate_all_lenders.py
│   ├── test_evaluate_parallel_execution
│   ├── test_evaluate_handles_single_lender_error
│   ├── test_evaluate_continues_on_error
│   └── test_evaluate_skips_on_derive_failure
└── test_persist_and_rank.py
    ├── test_persist_match_results
    ├── test_rank_eligible_lenders
    ├── test_rank_ineligible_no_rank
    ├── test_update_application_status
    └── test_skips_on_evaluation_failure

backend/tests/integration/
└── test_evaluation_workflow.py
    ├── test_full_workflow_success
    ├── test_workflow_validation_failure
    ├── test_workflow_retries_on_db_error
    └── test_workflow_status_tracking
```

### Independence
This PR depends on PR-2 (models for persistence) and PR-5 (matching service). The workflow steps can be unit tested by mocking the Hatchet context and database session.

---

## PR-7: Backend API Endpoints

### Why We're Doing This
Expose the matching functionality through a RESTful API. The API provides endpoints for:
- Submitting loan applications and triggering evaluation
- Retrieving application details and processing status
- Viewing match results
- Managing lender policies (CRUD operations)

### How It Will Be Done

#### Step 1: Create Application Endpoints
CRUD operations for loan applications.

```python
# backend/app/api/routes/applications.py
@router.post("/", response_model=ApplicationResponse)
async def submit_application(
    application_input: LoanApplicationInput,
    db: DbSession,
    hatchet: Hatchet = Depends(get_hatchet)
):
    """Submit new application and trigger evaluation workflow."""
    ...

@router.get("/", response_model=PaginatedResponse[ApplicationSummary])
async def list_applications(db: DbSession, skip: int = 0, limit: int = 20):
    """List all applications with pagination."""
    ...

@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_application(application_id: UUID, db: DbSession):
    """Get full application details."""
    ...

@router.get("/{application_id}/status", response_model=ApplicationStatus)
async def get_application_status(application_id: UUID, db: DbSession):
    """Get current processing status."""
    ...

@router.get("/{application_id}/results", response_model=MatchingResultsResponse)
async def get_match_results(application_id: UUID, db: DbSession):
    """Get matching results for an application."""
    ...
```

#### Step 2: Create Lender Endpoints
Management endpoints for lender policies.

```python
# backend/app/api/routes/lenders.py
@router.get("/", response_model=list[LenderSummary])
async def list_lenders(db: DbSession):
    """List all lenders with program counts."""
    ...

@router.get("/{lender_id}", response_model=LenderDetail)
async def get_lender(lender_id: str, db: DbSession):
    """Get lender details with full policy."""
    ...

@router.post("/", response_model=LenderDetail)
async def create_lender(lender_input: LenderCreate, db: DbSession):
    """Create new lender with policy."""
    ...

@router.put("/{lender_id}", response_model=LenderDetail)
async def update_lender(lender_id: str, lender_update: LenderUpdate, db: DbSession):
    """Update existing lender."""
    ...

@router.patch("/{lender_id}/status", response_model=LenderDetail)
async def toggle_lender_status(lender_id: str, db: DbSession):
    """Toggle lender active/inactive."""
    ...

@router.delete("/{lender_id}")
async def delete_lender(lender_id: str, db: DbSession):
    """Soft delete a lender."""
    ...
```

#### Step 3: Wire Up Routes to Main App
Register routers with the FastAPI application.

```python
# backend/app/api/__init__.py
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(lenders.router, prefix="/lenders", tags=["Lenders"])
```

### Files to Create/Modify

```
backend/app/api/
├── __init__.py              # API router aggregation
├── deps.py                  # Common dependencies
└── routes/
    ├── __init__.py
    ├── applications.py      # Application endpoints
    └── lenders.py           # Lender endpoints

backend/app/services/
├── application_service.py   # Application CRUD logic
└── lender_service.py        # Lender CRUD logic

backend/app/main.py          # Include API router
```

### Unit Tests

```
backend/tests/unit/api/
├── __init__.py
├── test_applications.py
│   ├── test_submit_application_success
│   ├── test_submit_application_validation_error
│   ├── test_list_applications_pagination
│   ├── test_get_application_found
│   ├── test_get_application_not_found
│   ├── test_get_application_status_pending
│   ├── test_get_application_status_completed
│   ├── test_get_match_results_found
│   └── test_get_match_results_processing
└── test_lenders.py
    ├── test_list_lenders
    ├── test_get_lender_found
    ├── test_get_lender_not_found
    ├── test_create_lender_success
    ├── test_create_lender_duplicate_id
    ├── test_update_lender_success
    ├── test_update_lender_not_found
    ├── test_toggle_status
    └── test_delete_lender

backend/tests/integration/api/
├── __init__.py
├── test_application_flow.py
│   ├── test_submit_and_get_results
│   ├── test_application_lifecycle
│   └── test_concurrent_submissions
└── test_lender_management.py
    ├── test_create_and_list_lenders
    └── test_update_affects_matching
```

### Independence
This PR depends on PR-2 (models), PR-5 (matching service), and PR-6 (workflow). API endpoints can be developed with mock services, allowing parallel development with workflow implementation.

---

## PR-8: Frontend Application Form

### Why We're Doing This
The application form is the primary user interface for submitting loan applications. A well-designed multi-step form:
- Guides users through complex data entry
- Validates input before submission
- Provides clear feedback on errors
- Reduces abandonment through progressive disclosure

### How It Will Be Done

#### Step 1: Define TypeScript Types
Create type definitions matching backend schemas.

```typescript
// frontend/src/types/application.ts
export interface LoanApplicationInput {
  // Applicant
  fico_score: number;
  transunion_score?: number;
  paynet_score?: number;
  is_homeowner: boolean;
  is_us_citizen: boolean;
  // Business
  business_name: string;
  state: string;
  industry_code: string;
  years_in_business: number;
  // ... equipment, credit history, loan request
}

export type EquipmentCategory =
  | 'class_8_truck'
  | 'trailer'
  | 'construction'
  | 'vocational'
  | 'other';

export type TransactionType =
  | 'purchase'
  | 'refinance'
  | 'sale_leaseback';
```

#### Step 2: Create API Client Functions
Typed functions for API calls.

```typescript
// frontend/src/api/applications.ts
export async function submitApplication(
  input: LoanApplicationInput
): Promise<ApplicationResponse> {
  const response = await client.post('/applications', input);
  return response.data;
}

export async function getApplicationStatus(
  applicationId: string
): Promise<ApplicationStatus> {
  const response = await client.get(`/applications/${applicationId}/status`);
  return response.data;
}
```

#### Step 3: Implement Form Sections
Each section is a separate component with its own validation.

| Component | Fields |
|-----------|--------|
| `ApplicantSection` | FICO, TransUnion, PayNet scores, homeowner, citizen |
| `BusinessSection` | Name, state, industry, years, revenue, fleet size |
| `EquipmentSection` | Category, type, year, mileage, hours, condition |
| `CreditHistorySection` | Bankruptcy, judgements, foreclosure, repos, liens |
| `LoanRequestSection` | Amount, term, transaction type, private party, down payment |

#### Step 4: Create Multi-Step Form Container
Orchestrate section navigation with validation.

```typescript
// frontend/src/components/application/ApplicationForm.tsx
export function ApplicationForm() {
  const [step, setStep] = useState(1);
  const methods = useForm<LoanApplicationInput>({
    resolver: zodResolver(applicationSchema)
  });

  const sections = [
    { title: 'Applicant', component: ApplicantSection },
    { title: 'Business', component: BusinessSection },
    { title: 'Equipment', component: EquipmentSection },
    { title: 'Credit History', component: CreditHistorySection },
    { title: 'Loan Request', component: LoanRequestSection },
  ];
  // ...
}
```

### Files to Create/Modify

```
frontend/src/types/
├── application.ts           # Application-related types
├── common.ts                # Shared types
└── index.ts                 # Export all types

frontend/src/api/
├── applications.ts          # Application API functions
└── types.ts                 # API response types

frontend/src/components/application/
├── index.ts                 # Export all components
├── ApplicationForm.tsx      # Multi-step form container
├── ApplicantSection.tsx     # Credit scores, homeowner
├── BusinessSection.tsx      # Business details
├── EquipmentSection.tsx     # Equipment details
├── CreditHistorySection.tsx # Credit history flags
├── LoanRequestSection.tsx   # Loan amount, term
├── FormProgress.tsx         # Progress indicator
└── FormNavigation.tsx       # Next/Back buttons

frontend/src/pages/
└── ApplicationPage.tsx      # Application form page

frontend/src/lib/
└── validation.ts            # Zod schemas for form validation
```

### Unit Tests

```
frontend/src/__tests__/components/application/
├── ApplicationForm.test.tsx
│   ├── renders_all_steps
│   ├── navigates_between_steps
│   ├── validates_before_next_step
│   ├── submits_complete_form
│   └── shows_error_on_api_failure
├── ApplicantSection.test.tsx
│   ├── renders_all_fields
│   ├── validates_fico_required
│   ├── validates_fico_range
│   ├── homeowner_toggle_works
│   └── citizen_toggle_works
├── BusinessSection.test.tsx
│   ├── renders_all_fields
│   ├── validates_business_name_required
│   ├── state_dropdown_works
│   ├── industry_dropdown_works
│   └── years_in_business_accepts_decimal
├── EquipmentSection.test.tsx
│   ├── renders_all_fields
│   ├── category_dropdown_works
│   ├── shows_mileage_for_truck
│   ├── shows_hours_for_construction
│   └── validates_year_range
├── CreditHistorySection.test.tsx
│   ├── renders_all_flags
│   ├── bankruptcy_shows_details_when_yes
│   ├── judgement_shows_amount_when_yes
│   └── all_toggles_work_independently
└── LoanRequestSection.test.tsx
    ├── renders_all_fields
    ├── validates_loan_amount_required
    ├── transaction_type_dropdown_works
    ├── private_party_toggle_works
    └── down_payment_accepts_decimal

frontend/src/__tests__/api/
└── applications.test.ts
    ├── submitApplication_success
    ├── submitApplication_validation_error
    ├── getApplicationStatus_success
    └── getApplicationStatus_not_found

frontend/src/__tests__/lib/
└── validation.test.ts
    ├── application_schema_valid_data
    ├── application_schema_missing_required
    ├── application_schema_invalid_fico_range
    └── application_schema_conditional_fields
```

### Independence
This PR depends on PR-7 (API endpoints) for integration. However, all components and validation can be developed and tested with mock API responses, allowing parallel development.

---

## PR-9: Frontend Results & Policy Management

### Why We're Doing This
The results display and policy management UI complete the user experience:
- Results display shows matched/unmatched lenders with detailed reasoning
- Criteria breakdown helps users understand why they qualified or didn't
- Policy management enables admins to view and edit lender configurations

### How It Will Be Done

#### Step 1: Create Results Display Components

```typescript
// frontend/src/components/results/MatchingResults.tsx
export function MatchingResults({ applicationId }: Props) {
  const { data, isLoading } = useQuery(
    ['matchResults', applicationId],
    () => fetchMatchResults(applicationId)
  );

  return (
    <div>
      <ResultsSummary data={data} />
      <EligibleLenders matches={data.matches.filter(m => m.is_eligible)} />
      <IneligibleLenders matches={data.matches.filter(m => !m.is_eligible)} />
    </div>
  );
}

// frontend/src/components/results/CriteriaBreakdown.tsx
export function CriteriaBreakdown({ criteria }: Props) {
  return (
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
          <CriterionRow key={key} criterion={result} />
        ))}
      </tbody>
    </table>
  );
}
```

#### Step 2: Create Lender Management Pages

```typescript
// frontend/src/pages/admin/LenderListPage.tsx
export function LenderListPage() {
  const { data: lenders } = useQuery('lenders', fetchLenders);

  return (
    <div>
      <header>
        <h1>Lender Policies</h1>
        <Button onClick={() => navigate('/admin/lenders/new')}>Add New</Button>
      </header>
      <LenderTable lenders={lenders} />
    </div>
  );
}

// frontend/src/pages/admin/LenderDetailPage.tsx
export function LenderDetailPage() {
  const { lenderId } = useParams();
  const { data: lender } = useQuery(['lender', lenderId], () => fetchLender(lenderId));
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div>
      <LenderHeader lender={lender} onEdit={() => setIsEditing(true)} />
      <LenderPrograms programs={lender.programs} isEditing={isEditing} />
      <LenderRestrictions restrictions={lender.restrictions} isEditing={isEditing} />
      <EquipmentMatrices matrices={lender.equipment_matrices} isEditing={isEditing} />
    </div>
  );
}
```

#### Step 3: Create Admin Components
Reusable components for policy editing.

| Component | Purpose |
|-----------|---------|
| `ProgramCard` | Display/edit single program |
| `CriteriaEditor` | Edit criteria configuration |
| `RestrictionsEditor` | Edit state/industry restrictions |
| `EquipmentMatrixEditor` | Edit term matrices |

### Files to Create/Modify

```
frontend/src/types/
├── matching.ts              # Match result types
└── lender.ts                # Lender and policy types

frontend/src/api/
├── lenders.ts               # Lender API functions
└── matching.ts              # Matching results API

frontend/src/components/results/
├── index.ts
├── MatchingResults.tsx      # Results container
├── ResultsSummary.tsx       # Summary header
├── LenderCard.tsx           # Single lender result
├── ScoreGauge.tsx           # Visual score display
├── CriteriaBreakdown.tsx    # Detailed criteria table
└── RejectionReasons.tsx     # Rejection summary

frontend/src/components/admin/
├── index.ts
├── LenderTable.tsx          # Lender list table
├── LenderForm.tsx           # Create/edit lender form
├── ProgramCard.tsx          # Program display/edit
├── CriteriaEditor.tsx       # Criteria configuration
├── RestrictionsEditor.tsx   # Restrictions configuration
└── EquipmentMatrixEditor.tsx # Equipment matrix editor

frontend/src/pages/
├── ResultsPage.tsx          # Results display page
├── ApplicationDetailPage.tsx # Application details
└── admin/
    ├── LenderListPage.tsx   # List all lenders
    ├── LenderDetailPage.tsx # View/edit lender
    └── LenderCreatePage.tsx # Create new lender
```

### Unit Tests

```
frontend/src/__tests__/components/results/
├── MatchingResults.test.tsx
│   ├── renders_loading_state
│   ├── renders_eligible_lenders
│   ├── renders_ineligible_lenders_collapsed
│   ├── expands_ineligible_section
│   └── highlights_best_match
├── LenderCard.test.tsx
│   ├── renders_lender_name_and_score
│   ├── shows_matched_program
│   ├── expands_to_show_details
│   └── shows_rejection_reasons_when_ineligible
├── ScoreGauge.test.tsx
│   ├── renders_score_value
│   ├── shows_correct_color_for_score
│   └── handles_zero_score
├── CriteriaBreakdown.test.tsx
│   ├── renders_all_criteria
│   ├── shows_pass_icon_for_passed
│   ├── shows_fail_icon_for_failed
│   └── shows_detailed_message
└── RejectionReasons.test.tsx
    ├── renders_all_reasons
    └── handles_empty_reasons

frontend/src/__tests__/components/admin/
├── LenderTable.test.tsx
│   ├── renders_all_lenders
│   ├── shows_program_count
│   ├── shows_status_badge
│   └── navigates_to_detail_on_click
├── LenderForm.test.tsx
│   ├── renders_all_fields
│   ├── validates_required_fields
│   └── submits_form_data
├── ProgramCard.test.tsx
│   ├── renders_program_details
│   ├── shows_criteria_in_view_mode
│   └── enables_editing_in_edit_mode
├── CriteriaEditor.test.tsx
│   ├── renders_current_criteria
│   ├── adds_new_criterion
│   └── removes_criterion
└── EquipmentMatrixEditor.test.tsx
    ├── renders_matrix_entries
    ├── adds_new_entry
    └── validates_entry_ranges

frontend/src/__tests__/pages/
├── ResultsPage.test.tsx
│   ├── renders_results_for_application
│   └── handles_application_not_found
└── admin/
    ├── LenderListPage.test.tsx
    │   ├── renders_lender_list
    │   └── add_button_navigates
    └── LenderDetailPage.test.tsx
        ├── renders_lender_details
        ├── enter_edit_mode
        └── save_changes
```

### Independence
This PR depends on PR-7 (API endpoints) and PR-8 (form establishes routing patterns). Results components can be developed with mock data while the API is being built.

---

## PR-10: E2E Testing & Polish

### Why We're Doing This
End-to-end tests validate the complete system works together. This final PR ensures:
- Full user flows work correctly
- Integration between frontend and backend is solid
- Edge cases are handled gracefully
- Documentation is complete

### How It Will Be Done

#### Step 1: Set Up E2E Testing Framework
Configure Playwright or Cypress for E2E tests.

```typescript
// e2e/playwright.config.ts
export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://localhost:3000',
  },
  webServer: {
    command: 'docker-compose up',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

#### Step 2: Write E2E Test Scenarios

```typescript
// e2e/tests/application-flow.spec.ts
test.describe('Application Flow', () => {
  test('complete application submission and results', async ({ page }) => {
    // Navigate to application form
    await page.goto('/apply');

    // Fill Step 1: Applicant
    await page.fill('[data-testid="fico-score"]', '720');
    await page.click('[data-testid="is-homeowner-yes"]');
    await page.click('[data-testid="next-step"]');

    // Fill Step 2-5...

    // Submit
    await page.click('[data-testid="submit-application"]');

    // Wait for results
    await page.waitForURL(/\/results\//);

    // Verify results displayed
    await expect(page.locator('[data-testid="eligible-count"]')).toBeVisible();
  });
});
```

#### Step 3: Write Integration Test Scenarios

| Scenario | Description |
|----------|-------------|
| CA applicant | Verify CA excluded from Citizens/Apex |
| Startup with experience | Verify matches startup programs |
| High mileage truck | Verify term matrix applies correctly |
| Bankruptcy 3 years | Verify excluded from most lenders |
| Full qualification | Verify highest score calculation |

#### Step 4: Performance Optimization
- Add database indexes for common queries
- Implement response caching where appropriate
- Optimize frontend bundle size

### Files to Create/Modify

```
e2e/
├── playwright.config.ts
├── tests/
│   ├── application-flow.spec.ts
│   ├── results-display.spec.ts
│   ├── lender-management.spec.ts
│   └── edge-cases.spec.ts
└── fixtures/
    ├── applications.json
    └── expected-results.json

backend/
├── tests/e2e/
│   └── test_full_flow.py
└── app/models/
    └── (add indexes)

docs/
├── API.md
├── DEPLOYMENT.md
└── ADDING_LENDERS.md
```

### Test Scenarios

```
e2e/tests/
├── application-flow.spec.ts
│   ├── complete_application_submission
│   ├── form_validation_errors
│   ├── form_navigation_back_preserves_data
│   ├── submit_triggers_processing
│   └── results_display_after_processing
├── results-display.spec.ts
│   ├── shows_eligible_lenders_ranked
│   ├── shows_ineligible_with_reasons
│   ├── criteria_breakdown_accurate
│   ├── expands_lender_details
│   └── best_match_highlighted
├── lender-management.spec.ts
│   ├── list_all_lenders
│   ├── view_lender_details
│   ├── edit_lender_criteria
│   ├── toggle_lender_status
│   └── add_new_lender
└── edge-cases.spec.ts
    ├── ca_applicant_excluded_from_restricted_lenders
    ├── startup_matches_startup_programs_only
    ├── high_mileage_truck_reduced_term
    ├── recent_bankruptcy_excluded
    ├── no_paynet_uses_alternative_criteria
    └── trucking_requires_fleet_and_cdl
```

### Independence
This PR depends on all previous PRs being merged. It represents the final integration testing and polish phase.

---

## Development Parallelization

The following PRs can be developed in parallel:

```
                    PR-1 (Setup) ✓
                         │
            ┌────────────┼────────────┐
            │            │            │
         PR-2         PR-3         PR-8*
       (Models)    (Rule Engine)  (Frontend Form)
            │            │            │
            │            │            │
            └────────┬───┘            │
                     │                │
                  PR-4             PR-9*
               (Policies)      (Frontend Results)
                     │
            ┌────────┴────────┐
            │                 │
         PR-5              PR-6
      (Matching)        (Workflow)
            │                 │
            └────────┬────────┘
                     │
                  PR-7
                 (API)
                     │
            ┌────────┴────────┐
            │                 │
         PR-8              PR-9
      (Form Integration)   (Results Integration)
                     │
                  PR-10
                 (E2E)

* Can start with mocks before API is ready
```

### Parallel Tracks

**Track A (Backend Core):** PR-2 → PR-5 → PR-6 → PR-7
**Track B (Rule Engine):** PR-3 → PR-4 → (merges into PR-5)
**Track C (Frontend):** PR-8* → PR-9* → (integrates after PR-7)

---

## Merge Order

1. **PR-1** - Project Setup (COMPLETED)
2. **PR-2** - Database Models & Schemas
3. **PR-3** - Rule Engine Foundation (can parallel with PR-2)
4. **PR-4** - Policy System & Lender Configurations (after PR-3)
5. **PR-5** - Matching Engine & Service (after PR-2, PR-3, PR-4)
6. **PR-6** - Hatchet Workflow Integration (after PR-2, PR-5)
7. **PR-7** - Backend API Endpoints (after PR-5, PR-6)
8. **PR-8** - Frontend Application Form (after PR-7)
9. **PR-9** - Frontend Results & Policy Management (after PR-7, PR-8)
10. **PR-10** - E2E Testing & Polish (after all)

---

## Success Criteria Per PR

| PR | Criteria |
|----|----------|
| PR-2 | All models created, migrations run, schema validation passes |
| PR-3 | All rules implemented, 100% unit test coverage on rules |
| PR-4 | All 5 lender YAMLs valid, policy loader works |
| PR-5 | Matching returns correct results for test scenarios |
| PR-6 | Workflow completes successfully, retries work |
| PR-7 | All endpoints return correct responses, OpenAPI docs complete |
| PR-8 | Form submits successfully, validation works |
| PR-9 | Results display correctly, admin can edit policies |
| PR-10 | All E2E tests pass, documentation complete |
