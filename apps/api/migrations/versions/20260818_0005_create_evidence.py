"""create evidence tables

Revision ID: 20260818_0005
Revises: 20260818_0004
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0005"
down_revision: str | None = "20260818_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evidence_items_evidence_type"), "evidence_items", ["evidence_type"], unique=False
    )

    op.create_table(
        "document_evidence_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("freshness", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_by_id", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_evidence_links_document_id"),
        "document_evidence_links",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_evidence_links_evidence_id"),
        "document_evidence_links",
        ["evidence_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_evidence_links_status"),
        "document_evidence_links",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_evidence_links_freshness"),
        "document_evidence_links",
        ["freshness"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_evidence_links_decided_by_id"),
        "document_evidence_links",
        ["decided_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_evidence_links_reviewed_by_id"),
        "document_evidence_links",
        ["reviewed_by_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_document_evidence_links_reviewed_by_id"), table_name="document_evidence_links"
    )
    op.drop_index(
        op.f("ix_document_evidence_links_decided_by_id"), table_name="document_evidence_links"
    )
    op.drop_index(
        op.f("ix_document_evidence_links_freshness"), table_name="document_evidence_links"
    )
    op.drop_index(op.f("ix_document_evidence_links_status"), table_name="document_evidence_links")
    op.drop_index(
        op.f("ix_document_evidence_links_evidence_id"), table_name="document_evidence_links"
    )
    op.drop_index(
        op.f("ix_document_evidence_links_document_id"), table_name="document_evidence_links"
    )
    op.drop_table("document_evidence_links")
    op.drop_index(op.f("ix_evidence_items_evidence_type"), table_name="evidence_items")
    op.drop_table("evidence_items")
