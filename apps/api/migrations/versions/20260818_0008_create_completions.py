"""create document completions

Revision ID: 20260818_0008
Revises: 20260818_0007
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0008"
down_revision: str | None = "20260818_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_completions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("external_edit_result_id", sa.Uuid(), nullable=False),
        sa.Column("original_format", sa.String(length=8), nullable=False),
        sa.Column("completed_by_id", sa.Uuid(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["completed_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["external_edit_result_id"], ["external_edit_results.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
        sa.UniqueConstraint("external_edit_result_id"),
    )
    op.create_index(
        op.f("ix_document_completions_document_id"),
        "document_completions",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_completions_external_edit_result_id"),
        "document_completions",
        ["external_edit_result_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_completions_completed_by_id"),
        "document_completions",
        ["completed_by_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_document_completions_completed_by_id"), table_name="document_completions"
    )
    op.drop_index(
        op.f("ix_document_completions_external_edit_result_id"), table_name="document_completions"
    )
    op.drop_index(op.f("ix_document_completions_document_id"), table_name="document_completions")
    op.drop_table("document_completions")
