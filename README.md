# Lender Matching Platform

A sophisticated loan application matching platform that evaluates applications against multiple lender policies to find the best financing options. The system uses a rule engine to match applications with lender programs based on credit criteria, business requirements, equipment specifications, and geographic restrictions.

## Overview

The platform enables:
- **Applicants** to submit loan applications with business, credit, and equipment details
- **Automatic matching** against 5+ lender policies with multiple programs each
- **Detailed results** showing eligibility, fit scores, and rejection reasons
- **Admin interface** for managing lender configurations

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│   FastAPI       │────▶│   PostgreSQL    │
│  React + Vite   │     │   Backend       │     │   Database      │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Rule Engine    │
                        │  + Policies     │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │    Hatchet      │
                        │   (Workflows)   │
                        └─────────────────┘
```

## Tech Stack

### Backend
- **Python 3.11+** - Core runtime
- **FastAPI** - Async REST API framework
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **Alembic** - Database migrations
- **Pydantic** - Request/response validation
- **Hatchet** - Workflow orchestration (optional)
- **YAML** - Lender policy configuration

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation

### Infrastructure
- **PostgreSQL** - Primary database
- **Docker** - Containerization
- **GitHub Actions** - CI/CD

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or Docker)

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup

**Backend:**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your database URL

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   │   ├── routes/
│   │   │   │   ├── applications.py  # Application submission & results
│   │   │   │   └── lenders.py       # Lender CRUD operations
│   │   │   └── deps.py       # Dependency injection
│   │   ├── core/             # Configuration
│   │   │   ├── config.py     # Settings from environment
│   │   │   ├── database.py   # SQLAlchemy async setup
│   │   │   └── hatchet.py    # Workflow client
│   │   ├── models/           # SQLAlchemy ORM models
│   │   │   ├── application.py    # LoanApplication
│   │   │   ├── business.py       # Business entity
│   │   │   ├── guarantor.py      # PersonalGuarantor with credit
│   │   │   ├── business_credit.py # Commercial credit scores
│   │   │   ├── lender.py         # Lender metadata
│   │   │   └── match_result.py   # Evaluation results
│   │   ├── schemas/          # Pydantic validation
│   │   │   ├── api.py        # API request/response schemas
│   │   │   ├── application.py
│   │   │   ├── business.py
│   │   │   └── matching.py
│   │   ├── policies/         # Lender configurations
│   │   │   ├── lenders/      # YAML policy files
│   │   │   │   ├── citizens_bank.yaml
│   │   │   │   ├── apex_commercial.yaml
│   │   │   │   ├── stearns_bank.yaml
│   │   │   │   ├── falcon_equipment.yaml
│   │   │   │   └── advantage_plus.yaml
│   │   │   ├── loader.py     # Policy file loader
│   │   │   └── schema.py     # Policy validation schemas
│   │   ├── rules/            # Rule engine
│   │   │   ├── engine.py     # Core rule evaluation
│   │   │   ├── criteria/     # Individual rule implementations
│   │   │   └── context_builder.py
│   │   ├── services/         # Business logic
│   │   │   ├── matching_service.py      # Lender matching orchestration
│   │   │   └── application_db_manager.py # Database operations
│   │   └── workflows/        # Hatchet workflows
│   │       ├── evaluation.py # 4-step evaluation workflow
│   │       └── triggers.py   # Workflow triggering
│   ├── tests/
│   │   ├── unit/             # Unit tests by module
│   │   ├── integration/      # Integration tests
│   │   └── conftest.py       # Test fixtures
│   ├── alembic/              # Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/              # API client
│       ├── components/       # Reusable UI components
│       │   ├── ApplicationForm/  # Multi-step form
│       │   ├── ResultsDisplay/   # Match results
│       │   └── LenderCard/
│       ├── pages/
│       │   ├── ApplicationPage.tsx  # Application form
│       │   ├── ResultsPage.tsx      # View results
│       │   └── admin/               # Admin pages
│       └── types/            # TypeScript definitions
└── docker-compose.yml
```

## API Endpoints

### Applications

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/applications/` | Submit new application |
| GET | `/api/v1/applications/` | List applications (paginated) |
| GET | `/api/v1/applications/{id}` | Get application details |
| GET | `/api/v1/applications/{id}/status` | Get processing status |
| GET | `/api/v1/applications/{id}/results` | Get matching results |

### Lenders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/lenders/` | List all lenders |
| GET | `/api/v1/lenders/{id}` | Get lender details |
| GET | `/api/v1/lenders/{id}/programs` | List lender programs |
| POST | `/api/v1/lenders/` | Create lender |
| PUT | `/api/v1/lenders/{id}` | Update lender |
| PATCH | `/api/v1/lenders/{id}/status` | Toggle active status |
| DELETE | `/api/v1/lenders/{id}` | Delete lender |

## Data Models

### Application Flow

```
ApplicationSubmitRequest
    ├── ApplicantInput (credit scores, CDL, citizenship)
    ├── BusinessInput (name, state, years, revenue)
    ├── CreditHistoryInput (bankruptcy, liens, judgements)
    ├── EquipmentInput (category, year, mileage)
    └── LoanRequestInput (amount, term, transaction type)
           │
           ▼
    ┌─────────────────┐
    │ Rule Engine     │ ◀── Lender Policies (YAML)
    │ Evaluation      │
    └────────┬────────┘
             │
             ▼
    MatchResult
        ├── is_eligible: bool
        ├── fit_score: 0-100
        ├── matched_program: Program details
        ├── criteria_results: Rule-by-rule breakdown
        └── rejection_reasons: Why not eligible
```

### Database Schema

```
businesses
    ├── id (UUID, PK)
    ├── legal_name, entity_type
    ├── industry_code, industry_name
    ├── state, city, zip_code
    ├── years_in_business, annual_revenue
    └── fleet_size

personal_guarantors
    ├── id (UUID, PK)
    ├── fico_score, transunion_score, experian_score, equifax_score
    ├── is_homeowner, is_us_citizen
    ├── has_cdl, cdl_years, industry_experience_years
    ├── has_bankruptcy, bankruptcy_discharge_date, bankruptcy_chapter
    └── has_foreclosure, has_repossession, has_tax_liens

loan_applications
    ├── id (UUID, PK)
    ├── application_number (unique)
    ├── business_id (FK), guarantor_id (FK)
    ├── loan_amount, requested_term_months
    ├── equipment_category, equipment_year, equipment_mileage
    ├── status (pending/processing/completed/error)
    └── created_at, processed_at

lenders
    ├── id (string, PK) - matches YAML filename
    ├── name, is_active
    ├── policy_file, policy_version
    └── contact_email, contact_phone

match_results
    ├── id (UUID, PK)
    ├── application_id (FK), lender_id (FK)
    ├── is_eligible, fit_score, rank
    ├── matched_program_id, matched_program_name
    ├── criteria_results (JSONB)
    └── rejection_reasons (JSONB array)
```

## Lender Policy Configuration

Policies are defined in YAML files under `backend/app/policies/lenders/`. Each file represents a lender with multiple programs.

### Example Policy Structure

```yaml
id: citizens_bank
name: "Citizens Bank"
version: 1
description: "Equipment Finance Program"
contact_email: "contact@example.com"

# Global restrictions (apply to all programs)
restrictions:
  geographic:
    excluded_states: ["CA"]
  industry:
    excluded_industries: ["cannabis"]
  transaction:
    allows_private_party: true

# Equipment term matrices
equipment_matrices:
  - category: class_8_truck
    entries:
      - max_mileage: 200000
        term_months: 60
      - max_mileage: 400000
        term_months: 48

# Lending programs
programs:
  - id: app_only_tier_1
    name: "Application Only - Tier 1"
    is_app_only: true
    min_amount: 15000
    max_amount: 75000

    # Program-specific criteria
    credit_score:
      type: fico
      min: 700

    criteria:
      business:
        min_time_in_business_years: 2
        requires_homeowner: true
      credit_history:
        bankruptcy_allowed: true
        min_years_since_bankruptcy: 4
```

### Supported Criteria Types

| Category | Criteria |
|----------|----------|
| **Credit Score** | FICO, TransUnion, Experian, Equifax, PayNet minimums |
| **Business** | Time in business, homeownership, CDL, US citizenship |
| **Credit History** | Bankruptcy (with discharge years), foreclosure, repos, liens |
| **Equipment** | Age limits, mileage limits, condition requirements |
| **Geographic** | Excluded/included states |
| **Industry** | Excluded/included industries |
| **Transaction** | Private party, sale-leaseback, refinance allowances |

## Evaluation Workflow

The application evaluation runs as a 4-step workflow:

1. **Validate Application** - Check required fields and data ranges
2. **Derive Features** - Calculate equipment age, startup status, etc.
3. **Evaluate Lenders** - Run application through each lender's rule engine
4. **Rank Results** - Sort eligible lenders by fit score

With Hatchet enabled, this runs asynchronously. Without Hatchet, it runs synchronously.

## Running Tests

```bash
# Backend unit tests
cd backend
source venv/bin/activate
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/services/test_application_db_manager.py -v

# Frontend tests
cd frontend
npm test
```

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `HATCHET_CLIENT_TOKEN` | Hatchet API token | Optional |
| `ENVIRONMENT` | development/staging/production | development |
| `LOG_LEVEL` | Logging verbosity | INFO |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | http://localhost:8000 |

## Development

### Adding a New Lender

1. Create YAML file: `backend/app/policies/lenders/{lender_id}.yaml`
2. Follow the schema in `_template.yaml`
3. Lender automatically loads on next API request

### Adding New Rule Criteria

1. Add field to `backend/app/policies/schema.py`
2. Implement evaluation in `backend/app/rules/criteria/`
3. Update context builder if needed
4. Add unit tests

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Troubleshooting

### Foreign Key Constraint on match_results

If you see `violates foreign key constraint "match_results_lender_id_fkey"`:
- The lenders table needs to be synced from YAML policies
- This happens automatically on application submission
- Manually sync: The `sync_lenders()` method in `ApplicationDBManager` handles this

### Hatchet Connection Issues

If Hatchet is not configured:
- The system falls back to synchronous execution
- Set `HATCHET_CLIENT_TOKEN` to enable async workflows
- Check logs for "Running evaluation synchronously"

## License

MIT
