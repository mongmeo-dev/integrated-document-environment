from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.domains.impacts.models import DocumentImpact, DocumentRelationship


class ImpactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, candidate: DocumentRelationship | DocumentImpact) -> None:
        self._session.add(candidate)

    async def list_relationships_by_document_id(
        self, document_id: UUID
    ) -> list[DocumentRelationship]:
        result = await self._session.execute(
            select(DocumentRelationship)
            .where(
                or_(
                    DocumentRelationship.source_document_id == document_id,
                    DocumentRelationship.target_document_id == document_id,
                )
            )
            .order_by(DocumentRelationship.created_at.desc())
        )
        return list(result.scalars())

    async def list_impacts_by_document_id(self, document_id: UUID) -> list[DocumentImpact]:
        result = await self._session.execute(
            select(DocumentImpact)
            .where(
                or_(
                    DocumentImpact.source_document_id == document_id,
                    DocumentImpact.target_document_id == document_id,
                )
            )
            .order_by(DocumentImpact.created_at.desc())
        )
        return list(result.scalars())

    async def get_relationship_by_id(self, relationship_id: UUID) -> DocumentRelationship | None:
        result = await self._session.execute(
            select(DocumentRelationship).where(DocumentRelationship.id == relationship_id)
        )
        return result.scalar_one_or_none()

    async def get_impact_by_id(self, impact_id: UUID) -> DocumentImpact | None:
        result = await self._session.execute(
            select(DocumentImpact).where(DocumentImpact.id == impact_id)
        )
        return result.scalar_one_or_none()
