from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.domains.impacts.models import DocumentImpact, DocumentRelationship
from ide_api.domains.impacts.repository import ImpactRepository
from ide_api.domains.impacts.schemas import (
    CandidateStatus,
    DocumentCandidatesResponse,
    DocumentImpactCandidateCreate,
    DocumentRelationshipCandidateCreate,
)


class DocumentRelationshipNotFoundError(Exception):
    pass


class DocumentImpactNotFoundError(Exception):
    pass


class InvalidCandidateTransitionError(Exception):
    pass


class InvalidModificationDecisionError(Exception):
    pass


class ImpactService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = ImpactRepository(session)

    async def create_relationship_candidate(
        self, *, data: DocumentRelationshipCandidateCreate
    ) -> DocumentRelationship:
        relationship = DocumentRelationship(
            source_document_id=data.source_document_id,
            source_location=data.source_location,
            target_document_id=data.target_document_id,
            target_location=data.target_location,
            relationship_type=data.relationship_type.value,
            reason=data.reason,
            status=CandidateStatus.CANDIDATE.value,
        )
        self._repository.add(relationship)
        await self._session.commit()
        return relationship

    async def create_impact_candidate(
        self, *, data: DocumentImpactCandidateCreate
    ) -> DocumentImpact:
        impact = DocumentImpact(
            source_document_id=data.source_document_id,
            source_location=data.source_location,
            target_document_id=data.target_document_id,
            target_location=data.target_location,
            reason=data.reason,
            proposed_modification=data.proposed_modification,
            status=CandidateStatus.CANDIDATE.value,
        )
        self._repository.add(impact)
        await self._session.commit()
        return impact

    async def list_document_candidates(self, *, document_id: UUID) -> DocumentCandidatesResponse:
        relationships = await self._repository.list_relationships_by_document_id(document_id)
        impacts = await self._repository.list_impacts_by_document_id(document_id)
        return DocumentCandidatesResponse(
            document_id=document_id,
            relationships=relationships,
            impacts=impacts,
        )

    async def confirm_relationship(
        self, *, relationship_id: UUID, decided_by_id: UUID
    ) -> DocumentRelationship:
        relationship = await self._get_relationship(relationship_id)
        await self._decide_candidate(relationship, CandidateStatus.CONFIRMED, decided_by_id)
        return relationship

    async def reject_relationship(
        self, *, relationship_id: UUID, decided_by_id: UUID
    ) -> DocumentRelationship:
        relationship = await self._get_relationship(relationship_id)
        await self._decide_candidate(relationship, CandidateStatus.REJECTED, decided_by_id)
        return relationship

    async def confirm_impact(self, *, impact_id: UUID, decided_by_id: UUID) -> DocumentImpact:
        impact = await self._get_impact(impact_id)
        await self._decide_candidate(impact, CandidateStatus.CONFIRMED, decided_by_id)
        return impact

    async def reject_impact(self, *, impact_id: UUID, decided_by_id: UUID) -> DocumentImpact:
        impact = await self._get_impact(impact_id)
        await self._decide_candidate(impact, CandidateStatus.REJECTED, decided_by_id)
        return impact

    async def mark_modification_required(
        self, *, impact_id: UUID, decided_by_id: UUID
    ) -> DocumentImpact:
        return await self._decide_modification(
            impact_id, required=True, decided_by_id=decided_by_id
        )

    async def mark_modification_not_required(
        self, *, impact_id: UUID, decided_by_id: UUID
    ) -> DocumentImpact:
        return await self._decide_modification(
            impact_id, required=False, decided_by_id=decided_by_id
        )

    async def _decide_candidate(
        self,
        candidate: DocumentRelationship | DocumentImpact,
        status: CandidateStatus,
        decided_by_id: UUID,
    ) -> None:
        if CandidateStatus(candidate.status) is not CandidateStatus.CANDIDATE:
            raise InvalidCandidateTransitionError

        candidate.status = status.value
        candidate.decided_at = datetime.now(UTC)
        candidate.decided_by_id = decided_by_id
        await self._session.commit()

    async def _decide_modification(
        self, impact_id: UUID, *, required: bool, decided_by_id: UUID
    ) -> DocumentImpact:
        impact = await self._get_impact(impact_id)
        if CandidateStatus(impact.status) is not CandidateStatus.CONFIRMED:
            raise InvalidModificationDecisionError
        if impact.modification_required is not None:
            raise InvalidModificationDecisionError

        impact.modification_required = required
        impact.modification_decided_at = datetime.now(UTC)
        impact.modification_decided_by_id = decided_by_id
        await self._session.commit()
        return impact

    async def _get_relationship(self, relationship_id: UUID) -> DocumentRelationship:
        relationship = await self._repository.get_relationship_by_id(relationship_id)
        if relationship is None:
            raise DocumentRelationshipNotFoundError
        return relationship

    async def _get_impact(self, impact_id: UUID) -> DocumentImpact:
        impact = await self._repository.get_impact_by_id(impact_id)
        if impact is None:
            raise DocumentImpactNotFoundError
        return impact
