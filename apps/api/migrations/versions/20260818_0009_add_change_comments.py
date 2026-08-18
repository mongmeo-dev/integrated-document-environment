"""add change comments

Revision ID: 20260818_0009
Revises: 20260818_0008
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0009"
down_revision: str | None = "20260818_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "change_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("change_request_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["change_request_id"],
            ["change_requests.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resolved_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_change_comments_change_request_id"),
        "change_comments",
        ["change_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_comments_author_id"),
        "change_comments",
        ["author_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_comments_assignee_id"),
        "change_comments",
        ["assignee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_comments_status"),
        "change_comments",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_comments_resolved_by_id"),
        "change_comments",
        ["resolved_by_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_change_comments_resolved_by_id"), table_name="change_comments")
    op.drop_index(op.f("ix_change_comments_status"), table_name="change_comments")
    op.drop_index(op.f("ix_change_comments_assignee_id"), table_name="change_comments")
    op.drop_index(op.f("ix_change_comments_author_id"), table_name="change_comments")
    op.drop_index(
        op.f("ix_change_comments_change_request_id"),
        table_name="change_comments",
    )
    op.drop_table("change_comments")
