from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ide_api.core.database import Base
from ide_api.domains.auth.models import User
from ide_api.domains.documents.models import Document
from ide_api.domains.formatting.models import ExternalEditResult


def _utc_now() -> datetime:
    return datetime.now(UTC)


class DocumentCompletion(Base):
    __tablename__ = "document_completions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    external_edit_result_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("external_edit_results.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    original_format: Mapped[str] = mapped_column(String(8), nullable=False)
    completed_by_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    document: Mapped[Document] = relationship()
    external_edit_result: Mapped[ExternalEditResult] = relationship()
    completed_by: Mapped[User] = relationship()
