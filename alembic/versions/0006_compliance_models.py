"""compliance models

Revision ID: 0006_compliance_models
Revises: 0005_obligation_relationships
Create Date: 2026-04-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_compliance_models"
down_revision = "0005_obligation_relationships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("jurisdiction", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_companies_name", "companies", ["name"], unique=False)

    op.create_table(
        "company_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=16), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_company_documents_company_id", "company_documents", ["company_id"], unique=False)

    op.create_table(
        "compliance_statuses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("obligation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["obligation_id"], ["obligations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "obligation_id", name="uq_company_obligation_status"),
    )
    op.create_index("ix_compliance_statuses_company_id", "compliance_statuses", ["company_id"], unique=False)
    op.create_index("ix_compliance_statuses_obligation_id", "compliance_statuses", ["obligation_id"], unique=False)
    op.create_index("ix_compliance_statuses_status", "compliance_statuses", ["status"], unique=False)
    op.create_index("ix_compliance_statuses_risk_level", "compliance_statuses", ["risk_level"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_compliance_statuses_risk_level", table_name="compliance_statuses")
    op.drop_index("ix_compliance_statuses_status", table_name="compliance_statuses")
    op.drop_index("ix_compliance_statuses_obligation_id", table_name="compliance_statuses")
    op.drop_index("ix_compliance_statuses_company_id", table_name="compliance_statuses")
    op.drop_table("compliance_statuses")

    op.drop_index("ix_company_documents_company_id", table_name="company_documents")
    op.drop_table("company_documents")

    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_table("companies")

