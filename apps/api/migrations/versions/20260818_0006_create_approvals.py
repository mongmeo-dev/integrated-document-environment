"""create approval tables

Revision ID: 20260818_0006
Revises: 20260818_0005
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0006"
down_revision: str | None = "20260818_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "approval_workflows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("is_started", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index(
        op.f("ix_approval_workflows_document_id"),
        "approval_workflows",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_approval_workflows_status"), "approval_workflows", ["status"], unique=False
    )

    op.create_table(
        "approval_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workflow_id"], ["approval_workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_id", "sequence", name="uq_approval_steps_workflow_sequence"),
    )
    op.create_index(
        op.f("ix_approval_steps_workflow_id"), "approval_steps", ["workflow_id"], unique=False
    )
    op.create_index(
        op.f("ix_approval_steps_assignee_id"), "approval_steps", ["assignee_id"], unique=False
    )
    op.create_index(op.f("ix_approval_steps_status"), "approval_steps", ["status"], unique=False)

    op.create_table(
        "approval_workflow_audits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("before_json", sa.JSON(), nullable=False),
        sa.Column("after_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workflow_id"], ["approval_workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_approval_workflow_audits_workflow_id"),
        "approval_workflow_audits",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_approval_workflow_audits_actor_id"),
        "approval_workflow_audits",
        ["actor_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_approval_workflow_audits_actor_id"), table_name="approval_workflow_audits"
    )
    op.drop_index(
        op.f("ix_approval_workflow_audits_workflow_id"), table_name="approval_workflow_audits"
    )
    op.drop_table("approval_workflow_audits")
    op.drop_index(op.f("ix_approval_steps_status"), table_name="approval_steps")
    op.drop_index(op.f("ix_approval_steps_assignee_id"), table_name="approval_steps")
    op.drop_index(op.f("ix_approval_steps_workflow_id"), table_name="approval_steps")
    op.drop_table("approval_steps")
    op.drop_index(op.f("ix_approval_workflows_status"), table_name="approval_workflows")
    op.drop_index(op.f("ix_approval_workflows_document_id"), table_name="approval_workflows")
    op.drop_table("approval_workflows")
