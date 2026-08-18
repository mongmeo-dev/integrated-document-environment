"""create document relationship and impact tables

Revision ID: 20260818_0004
Revises: 20260818_0003
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0004"
down_revision: str | None = "20260818_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), nullable=False),
        sa.Column("source_location", sa.Text(), nullable=False),
        sa.Column("target_document_id", sa.Uuid(), nullable=False),
        sa.Column("target_location", sa.Text(), nullable=False),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_relationships_source_document_id"),
        "document_relationships",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_relationships_target_document_id"),
        "document_relationships",
        ["target_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_relationships_relationship_type"),
        "document_relationships",
        ["relationship_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_relationships_status"),
        "document_relationships",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_relationships_decided_by_id"),
        "document_relationships",
        ["decided_by_id"],
        unique=False,
    )

    op.create_table(
        "document_impacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), nullable=False),
        sa.Column("source_location", sa.Text(), nullable=False),
        sa.Column("target_document_id", sa.Uuid(), nullable=False),
        sa.Column("target_location", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("proposed_modification", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("modification_required", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by_id", sa.Uuid(), nullable=True),
        sa.Column("modification_decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("modification_decided_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["modification_decided_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_impacts_source_document_id"),
        "document_impacts",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_impacts_target_document_id"),
        "document_impacts",
        ["target_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_impacts_status"), "document_impacts", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_document_impacts_decided_by_id"),
        "document_impacts",
        ["decided_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_impacts_modification_decided_by_id"),
        "document_impacts",
        ["modification_decided_by_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_document_impacts_modification_decided_by_id"), table_name="document_impacts"
    )
    op.drop_index(op.f("ix_document_impacts_decided_by_id"), table_name="document_impacts")
    op.drop_index(op.f("ix_document_impacts_status"), table_name="document_impacts")
    op.drop_index(op.f("ix_document_impacts_target_document_id"), table_name="document_impacts")
    op.drop_index(op.f("ix_document_impacts_source_document_id"), table_name="document_impacts")
    op.drop_table("document_impacts")
    op.drop_index(
        op.f("ix_document_relationships_decided_by_id"), table_name="document_relationships"
    )
    op.drop_index(op.f("ix_document_relationships_status"), table_name="document_relationships")
    op.drop_index(
        op.f("ix_document_relationships_relationship_type"), table_name="document_relationships"
    )
    op.drop_index(
        op.f("ix_document_relationships_target_document_id"), table_name="document_relationships"
    )
    op.drop_index(
        op.f("ix_document_relationships_source_document_id"), table_name="document_relationships"
    )
    op.drop_table("document_relationships")
