"""add relationship analysis runs

Revision ID: 20260820_0013
Revises: 20260819_0012
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260820_0013"
down_revision: str | None = "20260819_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "relationship_analysis_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), nullable=False),
        sa.Column("source_document_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["source_document_version_id"],
            ["document_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_document_version_id",
            "prompt_version",
            name="uq_relationship_analysis_run_version_prompt",
        ),
    )
    op.create_index(
        op.f("ix_relationship_analysis_runs_source_document_id"),
        "relationship_analysis_runs",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_relationship_analysis_runs_source_document_version_id"),
        "relationship_analysis_runs",
        ["source_document_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_relationship_analysis_runs_status"),
        "relationship_analysis_runs",
        ["status"],
        unique=False,
    )
    for table in ("document_relationships", "document_evidence_links"):
        op.add_column(table, sa.Column("analysis_run_id", sa.Uuid(), nullable=True))
        op.create_foreign_key(
            f"{table}_analysis_run_id_fkey",
            table,
            "relationship_analysis_runs",
            ["analysis_run_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            op.f(f"ix_{table}_analysis_run_id"),
            table,
            ["analysis_run_id"],
            unique=False,
        )


def downgrade() -> None:
    for table in ("document_evidence_links", "document_relationships"):
        op.drop_index(op.f(f"ix_{table}_analysis_run_id"), table_name=table)
        op.drop_constraint(
            f"{table}_analysis_run_id_fkey", table, type_="foreignkey"
        )
        op.drop_column(table, "analysis_run_id")
    op.drop_index(
        op.f("ix_relationship_analysis_runs_status"),
        table_name="relationship_analysis_runs",
    )
    op.drop_index(
        op.f("ix_relationship_analysis_runs_source_document_version_id"),
        table_name="relationship_analysis_runs",
    )
    op.drop_index(
        op.f("ix_relationship_analysis_runs_source_document_id"),
        table_name="relationship_analysis_runs",
    )
    op.drop_table("relationship_analysis_runs")
