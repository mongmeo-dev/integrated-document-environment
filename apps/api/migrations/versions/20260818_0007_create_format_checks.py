"""create format check tables

Revision ID: 20260818_0007
Revises: 20260818_0006
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0007"
down_revision: str | None = "20260818_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "external_edit_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("original_format", sa.String(length=8), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index(
        op.f("ix_external_edit_results_document_id"),
        "external_edit_results",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_external_edit_results_document_version_id"),
        "external_edit_results",
        ["document_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_external_edit_results_status"),
        "external_edit_results",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_external_edit_results_created_by_id"),
        "external_edit_results",
        ["created_by_id"],
        unique=False,
    )

    op.create_table(
        "format_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("external_edit_result_id", sa.Uuid(), nullable=False),
        sa.Column("automatic_check_completed", sa.Boolean(), nullable=False),
        sa.Column("visual_review", sa.String(length=16), nullable=False),
        sa.Column("unresolved_difference_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["external_edit_result_id"], ["external_edit_results.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_edit_result_id"),
    )
    op.create_index(
        op.f("ix_format_checks_external_edit_result_id"),
        "format_checks",
        ["external_edit_result_id"],
        unique=False,
    )

    op.create_table(
        "format_differences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("format_check_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("original_value", sa.Text(), nullable=False),
        sa.Column("proposed_value", sa.Text(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["format_check_id"], ["format_checks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_format_differences_format_check_id"),
        "format_differences",
        ["format_check_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_format_differences_category"),
        "format_differences",
        ["category"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_format_differences_category"), table_name="format_differences")
    op.drop_index(op.f("ix_format_differences_format_check_id"), table_name="format_differences")
    op.drop_table("format_differences")
    op.drop_index(op.f("ix_format_checks_external_edit_result_id"), table_name="format_checks")
    op.drop_table("format_checks")
    op.drop_index(
        op.f("ix_external_edit_results_created_by_id"), table_name="external_edit_results"
    )
    op.drop_index(op.f("ix_external_edit_results_status"), table_name="external_edit_results")
    op.drop_index(
        op.f("ix_external_edit_results_document_version_id"), table_name="external_edit_results"
    )
    op.drop_index(op.f("ix_external_edit_results_document_id"), table_name="external_edit_results")
    op.drop_table("external_edit_results")
