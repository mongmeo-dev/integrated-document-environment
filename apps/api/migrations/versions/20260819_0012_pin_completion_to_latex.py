"""pin completions to LaTeX revisions

Revision ID: 20260819_0012
Revises: 20260819_0011
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260819_0012"
down_revision: str | None = "20260819_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "document_completions",
        "external_edit_result_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.alter_column(
        "document_completions",
        "original_format",
        existing_type=sa.String(length=8),
        nullable=True,
    )
    op.drop_constraint(
        "document_completions_document_id_fkey",
        "document_completions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "document_completions_document_id_fkey",
        "document_completions",
        "documents",
        ["document_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.add_column(
        "document_completions",
        sa.Column("latex_revision_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "document_completions",
        sa.Column("compiled_pdf_sha256", sa.String(length=64), nullable=True),
    )
    op.create_foreign_key(
        "document_completions_latex_revision_id_fkey",
        "document_completions",
        "latex_revisions",
        ["latex_revision_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_document_completions_latex_revision_id",
        "document_completions",
        ["latex_revision_id"],
    )
    op.create_index(
        op.f("ix_document_completions_latex_revision_id"),
        "document_completions",
        ["latex_revision_id"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_document_completions_compiled_pdf_sha256",
        "document_completions",
        "compiled_pdf_sha256 IS NULL OR length(compiled_pdf_sha256) = 64",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_document_completions_compiled_pdf_sha256",
        "document_completions",
        type_="check",
    )
    op.drop_index(
        op.f("ix_document_completions_latex_revision_id"),
        table_name="document_completions",
    )
    op.drop_constraint(
        "uq_document_completions_latex_revision_id",
        "document_completions",
        type_="unique",
    )
    op.drop_constraint(
        "document_completions_latex_revision_id_fkey",
        "document_completions",
        type_="foreignkey",
    )
    op.drop_column("document_completions", "compiled_pdf_sha256")
    op.drop_column("document_completions", "latex_revision_id")
    op.drop_constraint(
        "document_completions_document_id_fkey",
        "document_completions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "document_completions_document_id_fkey",
        "document_completions",
        "documents",
        ["document_id"],
        ["id"],
        ondelete="CASCADE",
    )
