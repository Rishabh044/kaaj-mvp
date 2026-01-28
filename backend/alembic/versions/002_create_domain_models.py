"""Create domain models for lender matching platform.

Revision ID: 002_domain_models
Revises:
Create Date: 2026-01-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_domain_models"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create businesses table
    op.create_table(
        "businesses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("dba_name", sa.String(length=255), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("industry_code", sa.String(length=10), nullable=False),
        sa.Column("industry_name", sa.String(length=255), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("zip_code", sa.String(length=10), nullable=False),
        sa.Column("years_in_business", sa.Numeric(precision=4, scale=1), nullable=False),
        sa.Column("annual_revenue", sa.BigInteger(), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("fleet_size", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_businesses_state", "businesses", ["state"])
    op.create_index("ix_businesses_industry_code", "businesses", ["industry_code"])

    # Create personal_guarantors table
    op.create_table(
        "personal_guarantors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("ssn_last_four", sa.String(length=4), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("fico_score", sa.Integer(), nullable=True),
        sa.Column("transunion_score", sa.Integer(), nullable=True),
        sa.Column("experian_score", sa.Integer(), nullable=True),
        sa.Column("equifax_score", sa.Integer(), nullable=True),
        sa.Column("is_homeowner", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_us_citizen", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("has_bankruptcy", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bankruptcy_discharge_date", sa.Date(), nullable=True),
        sa.Column("bankruptcy_chapter", sa.String(length=10), nullable=True),
        sa.Column("has_open_judgements", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("judgement_amount", sa.Integer(), nullable=True),
        sa.Column("has_foreclosure", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("foreclosure_date", sa.Date(), nullable=True),
        sa.Column("has_repossession", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("repossession_date", sa.Date(), nullable=True),
        sa.Column("has_tax_liens", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tax_lien_amount", sa.Integer(), nullable=True),
        sa.Column("has_cdl", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cdl_years", sa.Integer(), nullable=True),
        sa.Column("industry_experience_years", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create business_credits table
    op.create_table(
        "business_credits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=False),
        sa.Column("paynet_score", sa.Integer(), nullable=True),
        sa.Column("paynet_master_score", sa.Integer(), nullable=True),
        sa.Column("duns_number", sa.String(length=9), nullable=True),
        sa.Column("dnb_rating", sa.String(length=10), nullable=True),
        sa.Column("paydex_score", sa.Integer(), nullable=True),
        sa.Column("trade_line_count", sa.Integer(), nullable=True),
        sa.Column("highest_credit", sa.Integer(), nullable=True),
        sa.Column("average_days_to_pay", sa.Integer(), nullable=True),
        sa.Column("has_slow_pays", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("slow_pay_count", sa.Integer(), nullable=True),
        sa.Column("report_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id"),
    )

    # Create lenders table
    op.create_table(
        "lenders",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("contact_name", sa.String(length=100), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("policy_file", sa.String(length=255), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("policy_last_updated", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lenders_is_active", "lenders", ["is_active"])

    # Create loan_applications table
    op.create_table(
        "loan_applications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_number", sa.String(length=30), nullable=False),
        sa.Column("business_id", sa.UUID(), nullable=False),
        sa.Column("guarantor_id", sa.UUID(), nullable=False),
        sa.Column("loan_amount", sa.Integer(), nullable=False),
        sa.Column("requested_term_months", sa.Integer(), nullable=True),
        sa.Column("down_payment_percent", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("is_private_party", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("equipment_category", sa.String(length=100), nullable=False),
        sa.Column("equipment_type", sa.String(length=100), nullable=False),
        sa.Column("equipment_make", sa.String(length=100), nullable=True),
        sa.Column("equipment_model", sa.String(length=100), nullable=True),
        sa.Column("equipment_year", sa.Integer(), nullable=False),
        sa.Column("equipment_mileage", sa.Integer(), nullable=True),
        sa.Column("equipment_hours", sa.Integer(), nullable=True),
        sa.Column("equipment_age_years", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("equipment_condition", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="'pending'"),
        sa.Column("submitted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guarantor_id"], ["personal_guarantors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_number"),
    )
    op.create_index("ix_loan_applications_status", "loan_applications", ["status"])
    op.create_index("ix_loan_applications_submitted_at", "loan_applications", ["submitted_at"])

    # Create match_results table
    op.create_table(
        "match_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("lender_id", sa.String(length=50), nullable=False),
        sa.Column("is_eligible", sa.Boolean(), nullable=False),
        sa.Column("matched_program_id", sa.String(length=50), nullable=True),
        sa.Column("matched_program_name", sa.String(length=255), nullable=True),
        sa.Column("fit_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("criteria_results", postgresql.JSONB(), nullable=False, server_default="'{}'"),
        sa.Column("rejection_reasons", postgresql.JSONB(), nullable=True, server_default="'[]'"),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["application_id"], ["loan_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lender_id"], ["lenders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_match_results_application_id", "match_results", ["application_id"])
    op.create_index("ix_match_results_lender_id", "match_results", ["lender_id"])
    op.create_index("ix_match_results_is_eligible", "match_results", ["is_eligible"])


def downgrade() -> None:
    op.drop_table("match_results")
    op.drop_table("loan_applications")
    op.drop_table("lenders")
    op.drop_table("business_credits")
    op.drop_table("personal_guarantors")
    op.drop_table("businesses")
