from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ide_api.core.database import Base
from ide_api.domains.auth.models import User
from ide_api.domains.documents.models import Document


def _utc_now() -> datetime:
    return datetime.now(UTC)


class LatexRevision(Base):
    __tablename__ = "latex_revisions"
    __table_args__ = (
        CheckConstraint(
            "origin IN ('latex_upload', 'docx_conversion', 'web_edit')",
            name="ck_latex_revisions_origin",
        ),
        CheckConstraint(
            "conversion_status IN ('not_required', 'pending_review', 'accepted', 'rejected')",
            name="ck_latex_revisions_conversion_status",
        ),
        CheckConstraint(
            "compile_status IN ('pending', 'succeeded', 'failed')",
            name="ck_latex_revisions_compile_status",
        ),
        CheckConstraint(
            "length(source_sha256) = 64",
            name="ck_latex_revisions_source_sha256",
        ),
        CheckConstraint(
            "compiled_pdf_sha256 IS NULL OR length(compiled_pdf_sha256) = 64",
            name="ck_latex_revisions_compiled_pdf_sha256",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_object_key: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    entrypoint: Mapped[str] = mapped_column(String(512), nullable=False)
    origin: Mapped[str] = mapped_column(String(32), nullable=False)
    conversion_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="not_required"
    )
    compile_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    compiled_pdf_object_key: Mapped[str | None] = mapped_column(
        String(1024), unique=True, nullable=True
    )
    compiled_pdf_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    compile_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        nullable=False,
    )

    document: Mapped[Document] = relationship()
    creator: Mapped[User] = relationship()
    conversion_reviews: Mapped[list[LatexConversionReview]] = relationship(
        back_populates="revision",
    )


class LatexConversionReview(Base):
    __tablename__ = "latex_conversion_reviews"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('accepted', 'rejected')",
            name="ck_latex_conversion_reviews_decision",
        ),
        CheckConstraint(
            "length(trim(reason)) > 0",
            name="ck_latex_conversion_reviews_reason",
        ),
        UniqueConstraint("revision_id", name="uq_latex_conversion_reviews_revision_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    revision_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("latex_revisions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        nullable=False,
    )

    revision: Mapped[LatexRevision] = relationship(back_populates="conversion_reviews")
    decider: Mapped[User] = relationship()
