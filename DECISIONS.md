# Architecture & Design Decisions

This document captures key decisions made during the MVP development, including prioritization choices, simplifications, and planned future enhancements.

## Lender Requirements Prioritized

The system was designed around real lender requirements from 5 equipment finance lenders. Here's what we prioritized:

### 1. Credit Score Requirements (High Priority)

**Implemented:**
- Multi-bureau support: FICO, TransUnion, Experian, Equifax
- PayNet scores for commercial credit
- Minimum score thresholds per program
- Different score types per lender (e.g., Citizens Bank uses TransUnion, others use FICO)

**Why:** Credit score is the #1 knockout criterion across all lenders. Every policy starts with a credit check.

### 2. Business Profile Criteria (High Priority)

**Implemented:**
- Time in business (years) with startup detection
- Homeownership requirement (common for app-only programs)
- CDL licensing (required for trucking, conditional otherwise)
- CDL years of experience
- Industry experience years
- US citizenship requirement
- Fleet size for trucking businesses

**Why:** These are the core underwriting criteria that differentiate program tiers. Citizens Bank has 4 distinct programs based on these factors.

### 3. Credit History Derogatory Events (High Priority)

**Implemented:**
- Bankruptcy with discharge date and chapter tracking
- Years since bankruptcy discharge calculation
- Active vs discharged bankruptcy distinction
- Open judgements with dollar amount limits
- Foreclosure history
- Repossession history
- Tax liens with amount tracking

**Why:** Lenders have specific thresholds (e.g., "BK discharged 5+ years ago is OK, 4 years is not"). This granularity is essential for accurate matching.

### 4. Geographic Restrictions (Medium Priority)

**Implemented:**
- State-level exclusions (e.g., Citizens Bank excludes California)
- State-level inclusions (whitelist approach)
- Uppercase normalization for consistency

**Why:** Simple to implement, commonly requested, and a hard knockout criterion.

### 5. Equipment Term Matrices (Medium Priority)

**Implemented:**
- Equipment category-based matrices
- Year-based term limits (newer = longer terms)
- Mileage-based term limits for trucks
- Multiple categories: Class 8 trucks, trailers, dump trucks, construction equipment

**Why:** Equipment age/condition directly affects loan terms offered. This is how lenders mitigate collateral risk.

### 6. Transaction Type Restrictions (Medium Priority)

**Implemented:**
- Private party sale allowance
- Sale-leaseback allowance
- Refinance transaction allowance

**Why:** Many lenders restrict transaction types. Private party sales often require additional documentation.

### 7. Industry Restrictions (Lower Priority)

**Implemented:**
- Industry exclusion lists (cannabis, marijuana, etc.)
- Industry inclusion lists (whitelist approach)

**Why:** Implemented but with simple string matching. Most lenders have short exclusion lists.

### 8. Loan Amount Limits (Lower Priority)

**Implemented:**
- Min/max amount per program
- Amount-based program routing (app-only vs full doc)

**Why:** Basic implementation for program eligibility. More sophisticated pricing would require additional logic.

---

## Simplifications Made

### 1. Single Guarantor Model

**What we simplified:** Only supporting one personal guarantor per application.

**Reality:** Some loans have multiple guarantors, co-signers, or corporate guarantees.

**Why simplified:**
- MVP scope - single guarantor covers 80%+ of use cases
- Database schema is simpler (1:1 relationship)
- Evaluation logic doesn't need to aggregate multiple credit profiles

**Impact:** Cannot model "if guarantor A has BK, guarantor B must have 700+ FICO" scenarios.

### 2. Static Policy Files (YAML)

**What we simplified:** Lender policies stored as static YAML files, not in the database.

**Reality:** Lenders update policies frequently; a database-driven approach would be more flexible.

**Why simplified:**
- Version control for policy changes (git history)
- Easy to review and audit policy configurations
- No admin UI needed for policy editing in MVP
- Pydantic validation catches errors at load time

**Impact:** Policy updates require code deployment. No real-time policy editing.

### 3. Synchronous Fallback Workflow

**What we simplified:** When Hatchet is not configured, evaluation runs synchronously in the API request.

**Reality:** True async workflows with job queues are essential for production.

**Why simplified:**
- Enables local development without Hatchet infrastructure
- Simplifies testing (no external dependencies)
- MVP can demonstrate matching logic without workflow complexity

**Impact:** Large batch processing would block the API. No retry/resume for failed evaluations.

### 4. Simplified Fit Score Calculation

**What we simplified:** Linear weighted scoring with fixed weights per lender.

**Reality:** Lenders have complex internal scoring models, risk tiers, and pricing matrices.

**Why simplified:**
- Demonstrates the concept of ranked recommendations
- Configurable weights per lender in YAML
- Clear, explainable scores

**Impact:** Fit scores are directional, not predictive of actual approval odds.

### 5. No Document Verification

**What we simplified:** Application data is trusted as-is. No document upload or verification.

**Reality:** Full-doc programs require bank statements, tax returns, proof of ownership.

**Why simplified:**
- MVP focuses on eligibility matching, not document processing
- OCR/document extraction is a separate major feature
- Reduces scope significantly

**Impact:** Cannot differentiate "app-only approved" from "full-doc required" with actual document review.

### 6. Basic Equipment Categorization

**What we simplified:** Equipment categories are strings matched against predefined lists.

**Reality:** Equipment has make, model, VIN, exact specifications that affect valuation.

**Why simplified:**
- Category-level matching is sufficient for initial filtering
- Detailed equipment valuation requires external data sources (NADA, equipment databases)

**Impact:** Cannot do precise equipment-based term calculations for edge cases.

### 7. No Rate/Pricing Calculation

**What we simplified:** No interest rate or payment calculation.

**Reality:** Lenders have complex rate sheets based on credit tier, term, equipment, etc.

**Why simplified:**
- Rate sheets are proprietary and frequently updated
- Implementing accurate pricing requires direct lender integration
- MVP focuses on "can they qualify" not "at what rate"

**Impact:** Users see eligibility and fit score, but not expected rates or payments.

### 8. Residence History Not Tracked

**What we simplified:** Citizens Bank requires "5 years at current residence" for non-homeowner program - not implemented.

**Reality:** Residence stability is a real underwriting criterion.

**Why simplified:**
- Adds complexity to guarantor model
- Would require address history collection
- Affects only one program variation

**Impact:** Non-homeowner program matching may be slightly less accurate.

---

## What We Would Add With More Time

### High Priority Additions

#### 1. Document Upload & Management
- File upload for bank statements, tax returns, equipment invoices
- Document type classification
- Secure storage with encryption
- Document status tracking per application

#### 2. Rate Sheet Integration
- Import lender rate sheets (CSV/Excel)
- Calculate estimated rates based on credit tier
- Show monthly payment estimates
- Rate comparison across lenders

#### 3. Real-time Policy Editing
- Admin UI for modifying lender criteria
- Policy versioning with audit trail
- A/B testing for policy changes
- Rollback capability

#### 4. Application Status Notifications
- Email notifications for status changes
- Webhook integrations for CRM systems
- SMS alerts for urgent updates

#### 5. Multiple Guarantor Support
- Add/remove guarantors per application
- Aggregate credit evaluation
- "Best of" or "average" scoring options
- Joint credit history handling

### Medium Priority Additions

#### 6. Equipment Valuation Integration
- NADA integration for equipment values
- Book value vs loan amount validation
- LTV (loan-to-value) calculations
- Equipment depreciation modeling

#### 7. Business Verification
- Secretary of State API integration
- Business registration validation
- EIN verification
- Years in business from incorporation date

#### 8. Credit Bureau Integration
- Soft pull for pre-qualification
- Hard pull orchestration
- Credit freeze detection
- Multi-bureau report aggregation

#### 9. Lender Portal
- Lender-specific login
- Policy self-service editing
- Application pipeline view
- Approval/decline actions

#### 10. Analytics Dashboard
- Application volume trends
- Approval rate by lender
- Common rejection reasons
- Geographic heat maps

### Lower Priority / Future Vision

#### 11. Machine Learning Enhancements
- Approval probability prediction
- Optimal lender recommendation
- Fraud detection signals
- Document classification AI

#### 12. Lender API Integrations
- Direct submission to lender systems
- Real-time decisioning
- Automated document forwarding
- Status sync from lender portals

#### 13. Mobile Application
- Native iOS/Android apps
- Camera-based document capture
- Push notifications
- Biometric authentication

#### 14. Multi-tenancy
- White-label deployments
- Tenant-specific lender configurations
- Custom branding per broker
- Isolated data environments

#### 15. Compliance & Audit
- ECOA compliance checking
- Adverse action notice generation
- Full audit trail export
- Regulatory reporting

---

## Technical Debt Acknowledged

1. **datetime.utcnow() deprecation** - Should migrate to timezone-aware datetimes
2. **Test fixture warnings** - pytest-asyncio event loop deprecation warnings
3. **No database connection pooling tuning** - Uses SQLAlchemy defaults
4. **Missing request rate limiting** - No API throttling implemented
5. **No caching layer** - Policy files reloaded on each request
6. **Hardcoded equipment categories** - Should be configurable
7. **No input sanitization beyond Pydantic** - XSS prevention not specifically addressed

---

## Key Design Principles Followed

1. **Policy as Configuration** - Business rules in YAML, not code
2. **Explicit over Implicit** - All criteria clearly defined, no magic defaults
3. **Fail Fast** - Pydantic validation catches errors at API boundary
4. **Audit Trail** - MatchResult stores detailed criteria evaluation
5. **Separation of Concerns** - Models, Schemas, Services, Rules are distinct layers
6. **Test Coverage** - Unit tests for models, schemas, services, and workflows
7. **Database Agnostic** - SQLAlchemy abstracts PostgreSQL specifics
8. **Async First** - FastAPI and SQLAlchemy async throughout
