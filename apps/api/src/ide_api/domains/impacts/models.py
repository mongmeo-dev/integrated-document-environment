from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ide_api.core.database import Base
from ide_api.domains.auth.models import User
from ide_api.domains.documents.models import Document


def _utc_now() -> datetime:
    return datetime.now(UTC)


class DocumentRelationship(Base):
    __tablename__ = "document_relationships"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_document_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_location: Mapped[str] = mapped_column(Text, nullable=False)
    target_document_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_location: Mapped[str] = mapped_column(Text, nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="candidate", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    source_document: Mapped[Document] = relationship(foreign_keys=[source_document_id])
    target_document: Mapped[Document] = relationship(foreign_keys=[target_document_id])
    decided_by: Mapped[User | None] = relationship(foreign_keys=[decided_by_id])


class DocumentImpact(Base):
    __tablename__ = "document_impacts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_document_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_location: Mapped[str] = mapped_column(Text, nullable=False)
    target_document_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_location: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_modification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="candidate", index=True)
    modification_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    modification_decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    modification_decided_by_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    source_document: Mapped[Document] = relationship(foreign_keys=[source_document_id])
    target_document: Mapped[Document] = relationship(foreign_keys=[target_document_id])
    decided_by: Mapped[User | None] = relationship(foreign_keys=[decided_by_id])
    modification_decided_by: Mapped[User | None] = relationship(
        foreign_keys=[modification_decided_by_id]
    )
