from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.domains.evidence.models import DocumentEvidenceLink, EvidenceItem


class EvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, item: EvidenceItem | DocumentEvidenceLink) -> None:
        self._session.add(item)

    async def list_evidence_items(self) -> list[EvidenceItem]:
        result = await self._session.execute(
            select(EvidenceItem).order_by(EvidenceItem.created_at.desc())
        )
        return list(result.scalars())

    async def get_evidence_item_by_id(self, evidence_id: UUID) -> EvidenceItem | None:
        result = await self._session.execute(
            select(EvidenceItem).where(EvidenceItem.id == evidence_id)
        )
        return result.scalar_one_or_none()

    async def list_links_by_document_id(self, document_id: UUID) -> list[DocumentEvidenceLink]:
        result = await self._session.execute(
            select(DocumentEvidenceLink)
            .where(DocumentEvidenceLink.document_id == document_id)
            .order_by(DocumentEvidenceLink.created_at.desc())
        )
        return list(result.scalars())

    async def list_links_by_evidence_id(self, evidence_id: UUID) -> list[DocumentEvidenceLink]:
        result = await self._session.execute(
            select(DocumentEvidenceLink)
            .where(DocumentEvidenceLink.evidence_id == evidence_id)
            .order_by(DocumentEvidenceLink.created_at.desc())
        )
        return list(result.scalars())

    async def get_link_by_id(self, link_id: UUID) -> DocumentEvidenceLink | None:
        result = await self._session.execute(
            select(DocumentEvidenceLink).where(DocumentEvidenceLink.id == link_id)
        )
        return result.scalar_one_or_none()
