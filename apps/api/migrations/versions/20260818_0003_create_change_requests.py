"""create change request tables

Revision ID: 20260818_0003
Revises: 20260818_0002
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0003"
down_revision: str | None = "20260818_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "change_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_change_requests_assignee_id"),
        "change_requests",
        ["assignee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_requests_document_id"),
        "change_requests",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_requests_requester_id"),
        "change_requests",
        ["requester_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_requests_status"),
        "change_requests",
        ["status"],
        unique=False,
    )

    op.create_table(
        "change_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("change_request_id", sa.Uuid(), nullable=False),
        sa.Column("proposed_text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["change_request_id"],
            ["change_requests.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_change_proposals_change_request_id"),
        "change_proposals",
        ["change_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_proposals_decided_by_id"),
        "change_proposals",
        ["decided_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_proposals_status"),
        "change_proposals",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_change_proposals_status"), table_name="change_proposals")
    op.drop_index(op.f("ix_change_proposals_decided_by_id"), table_name="change_proposals")
    op.drop_index(op.f("ix_change_proposals_change_request_id"), table_name="change_proposals")
    op.drop_table("change_proposals")
    op.drop_index(op.f("ix_change_requests_status"), table_name="change_requests")
    op.drop_index(op.f("ix_change_requests_requester_id"), table_name="change_requests")
    op.drop_index(op.f("ix_change_requests_document_id"), table_name="change_requests")
    op.drop_index(op.f("ix_change_requests_assignee_id"), table_name="change_requests")
    op.drop_table("change_requests")
