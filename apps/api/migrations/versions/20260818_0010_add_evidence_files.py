"""add evidence files

Revision ID: 20260818_0010
Revises: 20260818_0009
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260818_0010"
down_revision: str | None = "20260818_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evidence_items", sa.Column("object_key", sa.String(length=512), nullable=True))
    op.add_column(
        "evidence_items", sa.Column("original_filename", sa.String(length=255), nullable=True)
    )
    op.add_column("evidence_items", sa.Column("media_type", sa.String(length=255), nullable=True))
    op.add_column("evidence_items", sa.Column("size_bytes", sa.Integer(), nullable=True))
    op.add_column("evidence_items", sa.Column("sha256", sa.String(length=64), nullable=True))
    op.create_unique_constraint("uq_evidence_items_object_key", "evidence_items", ["object_key"])


def downgrade() -> None:
    op.drop_constraint("uq_evidence_items_object_key", "evidence_items", type_="unique")
    op.drop_column("evidence_items", "sha256")
    op.drop_column("evidence_items", "size_bytes")
    op.drop_column("evidence_items", "media_type")
    op.drop_column("evidence_items", "original_filename")
    op.drop_column("evidence_items", "object_key")
