from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ide_api.core.database import Base
from ide_api.domains.auth.models import User
from ide_api.domains.documents.models import Document, DocumentVersion


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ExternalEditResult(Base):
    __tablename__ = "external_edit_results"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_version_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_format: Mapped[str] = mapped_column(String(8), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="uploaded", index=True)
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
    document_version: Mapped[DocumentVersion] = relationship()
    creator: Mapped[User] = relationship()
    format_check: Mapped[FormatCheck] = relationship(
        back_populates="external_edit_result",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )


class FormatCheck(Base):
    __tablename__ = "format_checks"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    external_edit_result_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("external_edit_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    automatic_check_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visual_review: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    unresolved_difference_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    external_edit_result: Mapped[ExternalEditResult] = relationship(back_populates="format_check")
    differences: Mapped[list[FormatDifference]] = relationship(
        back_populates="format_check",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class FormatDifference(Base):
    __tablename__ = "format_differences"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    format_check_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("format_checks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    original_value: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_value: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        nullable=False,
    )

    format_check: Mapped[FormatCheck] = relationship(back_populates="differences")
