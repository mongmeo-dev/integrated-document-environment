from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.domains.approvals.models import ApprovalStep, ApprovalWorkflow
from ide_api.domains.changes.models import ChangeProposal, ChangeRequest
from ide_api.domains.completion.models import DocumentCompletion
from ide_api.domains.documents.models import Document, DocumentVersion
from ide_api.domains.evidence.models import DocumentEvidenceLink
from ide_api.domains.formatting.models import ExternalEditResult, FormatCheck
from ide_api.domains.impacts.models import DocumentImpact, DocumentRelationship


@dataclass(frozen=True)
class CompletionGateCounts:
    pending_change_requests: int
    pending_change_proposals: int
    pending_relationship_candidates: int
    pending_impact_candidates: int
    pending_evidence_candidates: int
    stale_evidence: int
    approval_workflows: int
    approval_steps: int
    incomplete_approval_steps: int
    incomplete_approval_workflows: int


class CompletionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, completion: DocumentCompletion) -> None:
        self._session.add(completion)

    async def document_exists(self, document_id: UUID) -> bool:
        return (
            await self._session.scalar(
                select(func.count()).select_from(Document).where(Document.id == document_id)
            )
        ) == 1

    async def get_external_result(
        self, external_edit_result_id: UUID
    ) -> tuple[ExternalEditResult, DocumentVersion, FormatCheck | None] | None:
        result = await self._session.execute(
            select(ExternalEditResult, DocumentVersion, FormatCheck)
            .join(DocumentVersion, ExternalEditResult.document_version_id == DocumentVersion.id)
            .outerjoin(FormatCheck, FormatCheck.external_edit_result_id == ExternalEditResult.id)
            .where(ExternalEditResult.id == external_edit_result_id)
        )
        return result.one_or_none()

    async def get_completion(self, document_id: UUID) -> DocumentCompletion | None:
        return await self._session.scalar(
            select(DocumentCompletion).where(DocumentCompletion.document_id == document_id)
        )

    async def get_gate_counts(self, document_id: UUID) -> CompletionGateCounts:
        pending_change_requests = await self._count(
            select(ChangeRequest).where(
                ChangeRequest.document_id == document_id,
                ChangeRequest.status.not_in(("accepted", "rejected")),
            )
        )
        pending_change_proposals = await self._count(
            select(ChangeProposal)
            .join(ChangeRequest, ChangeProposal.change_request_id == ChangeRequest.id)
            .where(
                ChangeRequest.document_id == document_id,
                ChangeProposal.status.not_in(("accepted", "rejected")),
            )
        )
        pending_relationship_candidates = await self._count(
            select(DocumentRelationship).where(
                or_(
                    DocumentRelationship.source_document_id == document_id,
                    DocumentRelationship.target_document_id == document_id,
                ),
                DocumentRelationship.status.not_in(("confirmed", "rejected")),
            )
        )
        pending_impact_candidates = await self._count(
            select(DocumentImpact).where(
                or_(
                    DocumentImpact.source_document_id == document_id,
                    DocumentImpact.target_document_id == document_id,
                ),
                DocumentImpact.status.not_in(("confirmed", "rejected")),
            )
        )
        pending_evidence_candidates = await self._count(
            select(DocumentEvidenceLink).where(
                DocumentEvidenceLink.document_id == document_id,
                DocumentEvidenceLink.status.not_in(("confirmed", "rejected")),
            )
        )
        stale_evidence = await self._count(
            select(DocumentEvidenceLink).where(
                DocumentEvidenceLink.document_id == document_id,
                DocumentEvidenceLink.freshness == "stale",
            )
        )
        approval_workflows = await self._count(
            select(ApprovalWorkflow).where(ApprovalWorkflow.document_id == document_id)
        )
        approval_steps = await self._count(
            select(ApprovalStep)
            .join(ApprovalWorkflow, ApprovalStep.workflow_id == ApprovalWorkflow.id)
            .where(ApprovalWorkflow.document_id == document_id)
        )
        incomplete_approval_steps = await self._count(
            select(ApprovalStep)
            .join(ApprovalWorkflow, ApprovalStep.workflow_id == ApprovalWorkflow.id)
            .where(ApprovalWorkflow.document_id == document_id, ApprovalStep.status != "completed")
        )
        incomplete_approval_workflows = await self._count(
            select(ApprovalWorkflow).where(
                ApprovalWorkflow.document_id == document_id,
                ApprovalWorkflow.status != "completed",
            )
        )
        return CompletionGateCounts(
            pending_change_requests=pending_change_requests,
            pending_change_proposals=pending_change_proposals,
            pending_relationship_candidates=pending_relationship_candidates,
            pending_impact_candidates=pending_impact_candidates,
            pending_evidence_candidates=pending_evidence_candidates,
            stale_evidence=stale_evidence,
            approval_workflows=approval_workflows,
            approval_steps=approval_steps,
            incomplete_approval_steps=incomplete_approval_steps,
            incomplete_approval_workflows=incomplete_approval_workflows,
        )

    async def _count(self, statement: object) -> int:
        return (
            await self._session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        )
