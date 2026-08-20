"""create latex projects

Revision ID: 20260819_0011
Revises: 20260818_0010
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260819_0011"
down_revision: str | None = "20260818_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "latex_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("source_object_key", sa.String(length=1024), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("entrypoint", sa.String(length=512), nullable=False),
        sa.Column("origin", sa.String(length=32), nullable=False),
        sa.Column("conversion_status", sa.String(length=32), nullable=False),
        sa.Column("compile_status", sa.String(length=32), nullable=False),
        sa.Column("compiled_pdf_object_key", sa.String(length=1024), nullable=True),
        sa.Column("compiled_pdf_sha256", sa.String(length=64), nullable=True),
        sa.Column("compile_log", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.CheckConstraint(
            "compile_status IN ('pending', 'succeeded', 'failed')",
            name="ck_latex_revisions_compile_status",
        ),
        sa.CheckConstraint(
            "conversion_status IN ('not_required', 'pending_review', 'accepted', 'rejected')",
            name="ck_latex_revisions_conversion_status",
        ),
        sa.CheckConstraint(
            "origin IN ('latex_upload', 'docx_conversion', 'web_edit')",
            name="ck_latex_revisions_origin",
        ),
        sa.CheckConstraint(
            "length(source_sha256) = 64",
            name="ck_latex_revisions_source_sha256",
        ),
        sa.CheckConstraint(
            "compiled_pdf_sha256 IS NULL OR length(compiled_pdf_sha256) = 64",
            name="ck_latex_revisions_compiled_pdf_sha256",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("compiled_pdf_object_key"),
        sa.UniqueConstraint("source_object_key"),
    )
    op.create_index(
        op.f("ix_latex_revisions_created_by_id"),
        "latex_revisions",
        ["created_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_latex_revisions_document_id"),
        "latex_revisions",
        ["document_id"],
        unique=False,
    )
    op.create_table(
        "latex_conversion_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("decided_by_id", sa.Uuid(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["revision_id"], ["latex_revisions.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "decision IN ('accepted', 'rejected')",
            name="ck_latex_conversion_reviews_decision",
        ),
        sa.CheckConstraint(
            "length(trim(reason)) > 0",
            name="ck_latex_conversion_reviews_reason",
        ),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "revision_id",
            name="uq_latex_conversion_reviews_revision_id",
        ),
    )
    op.create_index(
        op.f("ix_latex_conversion_reviews_decided_by_id"),
        "latex_conversion_reviews",
        ["decided_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_latex_conversion_reviews_revision_id"),
        "latex_conversion_reviews",
        ["revision_id"],
        unique=False,
    )
    op.execute(
        sa.text(
            "UPDATE document_versions "
            "SET input_kind = 'docx_import' "
            "WHERE input_kind = 'editable_docx'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE document_versions "
            "SET input_kind = 'editable_docx' "
            "WHERE input_kind = 'docx_import'"
        )
    )
    op.drop_index(
        op.f("ix_latex_conversion_reviews_revision_id"),
        table_name="latex_conversion_reviews",
    )
    op.drop_index(
        op.f("ix_latex_conversion_reviews_decided_by_id"),
        table_name="latex_conversion_reviews",
    )
    op.drop_table("latex_conversion_reviews")
    op.drop_index(op.f("ix_latex_revisions_document_id"), table_name="latex_revisions")
    op.drop_index(op.f("ix_latex_revisions_created_by_id"), table_name="latex_revisions")
    op.drop_table("latex_revisions")
