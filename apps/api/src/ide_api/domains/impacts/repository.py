from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.domains.impacts.models import (
    DocumentImpact,
    DocumentRelationship,
    RelationshipAnalysisRun,
)


class ImpactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, candidate: DocumentRelationship | DocumentImpact) -> None:
        self._session.add(candidate)

    def add_analysis_run(self, run: RelationshipAnalysisRun) -> None:
        self._session.add(run)

    async def get_analysis_run(
        self,
        *,
        source_document_version_id: UUID,
        prompt_version: str,
        for_update: bool = False,
    ) -> RelationshipAnalysisRun | None:
        statement = select(RelationshipAnalysisRun).where(
            RelationshipAnalysisRun.source_document_version_id == source_document_version_id,
            RelationshipAnalysisRun.prompt_version == prompt_version,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_latest_analysis_run(
        self, *, source_document_id: UUID
    ) -> RelationshipAnalysisRun | None:
        result = await self._session.execute(
            select(RelationshipAnalysisRun)
            .where(RelationshipAnalysisRun.source_document_id == source_document_id)
            .order_by(RelationshipAnalysisRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_queued_analysis_document_ids(self) -> list[UUID]:
        result = await self._session.execute(
            select(RelationshipAnalysisRun.source_document_id)
            .where(RelationshipAnalysisRun.status == "queued")
            .order_by(RelationshipAnalysisRun.created_at)
        )
        return list(result.scalars())

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
