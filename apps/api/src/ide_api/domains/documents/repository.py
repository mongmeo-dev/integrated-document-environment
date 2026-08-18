from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from ide_api.domains.documents.models import Document, DocumentVersion
from ide_api.domains.documents.schemas import DocumentStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, document: Document) -> None:
        self._session.add(document)

    async def get_by_id(self, document_id: UUID) -> Document | None:
        result = await self._session.execute(
            select(Document)
            .options(selectinload(Document.versions).selectinload(DocumentVersion.creator))
            .where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_latest_versions(
        self,
        *,
        document_status: DocumentStatus | None,
        query: str | None,
        limit: int,
        offset: int,
    ) -> list[Document]:
        latest_version_id = (
            select(DocumentVersion.id)
            .where(DocumentVersion.document_id == Document.id)
            .order_by(DocumentVersion.created_at.desc(), DocumentVersion.id.desc())
            .limit(1)
            .correlate(Document)
            .scalar_subquery()
        )
        statement: Select[tuple[Document]] = (
            select(Document)
            .join(DocumentVersion, DocumentVersion.id == latest_version_id)
            .options(contains_eager(Document.versions).selectinload(DocumentVersion.creator))
            .order_by(DocumentVersion.created_at.desc(), DocumentVersion.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if document_status is not None:
            statement = statement.where(DocumentVersion.status == document_status.value)
        if query:
            statement = statement.where(DocumentVersion.original_filename.ilike(f"%{query}%"))

        result = await self._session.execute(statement)
        return list(result.unique().scalars())
