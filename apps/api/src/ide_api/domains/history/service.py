from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.domains.approvals.models import ApprovalWorkflow, ApprovalWorkflowAudit
from ide_api.domains.changes.models import ChangeComment, ChangeProposal, ChangeRequest
from ide_api.domains.completion.models import DocumentCompletion
from ide_api.domains.evidence.models import DocumentEvidenceLink
from ide_api.domains.formatting.models import ExternalEditResult, FormatCheck
from ide_api.domains.history.schemas import HistoryEvent
from ide_api.domains.impacts.models import DocumentImpact, DocumentRelationship


def _safe_audit_data(data: dict) -> dict:
    sensitive_keys = {"objectkey", "password", "secret", "token"}

    def sanitize(value: object) -> object:
        if isinstance(value, dict):
            return {
                key: sanitize(item)
                for key, item in value.items()
                if not any(
                    sensitive_key in key.lower().replace("_", "")
                    for sensitive_key in sensitive_keys
                )
            }
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        return value

    return sanitize(data)


class HistoryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_events(
        self,
        *,
        document_id: UUID | None,
        event_filter: str | None,
        limit: int,
        offset: int,
    ) -> list[HistoryEvent]:
        events = await self._change_events(document_id)
        events.extend(await self._relationship_events(document_id))
        events.extend(await self._impact_events(document_id))
        events.extend(await self._evidence_events(document_id))
        events.extend(await self._approval_events(document_id))
        events.extend(await self._format_events(document_id))
        events.extend(await self._completion_events(document_id))
        if event_filter is not None:
            events = [event for event in events if event.type == event_filter]
        events.sort(key=lambda event: (event.occurred_at, str(event.id), event.type), reverse=True)
        return events[offset : offset + limit]

    async def _change_events(self, document_id: UUID | None) -> list[HistoryEvent]:
        request_statement = select(ChangeRequest)
        if document_id is not None:
            request_statement = request_statement.where(ChangeRequest.document_id == document_id)
        requests = list((await self._session.execute(request_statement)).scalars())
        request_ids = [request.id for request in requests]
        events = [
            HistoryEvent(
                id=request.id,
                type="change_request",
                document_id=request.document_id,
                actor_id=request.requester_id,
                occurred_at=request.created_at,
                reason=request.description,
                before=None,
                after={"status": request.status, "title": request.title},
                source_id=request.id,
            )
            for request in requests
        ]
        if not request_ids:
            return events

        proposals = list(
            (
                await self._session.execute(
                    select(ChangeProposal).where(ChangeProposal.change_request_id.in_(request_ids))
                )
            ).scalars()
        )
        request_document_ids = {request.id: request.document_id for request in requests}
        events.extend(
            HistoryEvent(
                id=proposal.id,
                type="change_proposal_decision",
                document_id=request_document_ids[proposal.change_request_id],
                actor_id=proposal.decided_by_id,
                occurred_at=proposal.decided_at,
                reason=proposal.rationale,
                before={"status": "candidate"},
                after={"status": proposal.status},
                source_id=proposal.id,
            )
            for proposal in proposals
            if proposal.decided_at is not None
        )

        comments = list(
            (
                await self._session.execute(
                    select(ChangeComment).where(ChangeComment.change_request_id.in_(request_ids))
                )
            ).scalars()
        )
        events.extend(
            HistoryEvent(
                id=comment.id,
                type="change_comment_status",
                document_id=request_document_ids[comment.change_request_id],
                actor_id=comment.resolved_by_id or comment.author_id,
                occurred_at=comment.resolved_at or comment.created_at,
                reason=comment.body,
                before={"status": "open"} if comment.resolved_at is not None else None,
                after={"status": comment.status},
                source_id=comment.id,
            )
            for comment in comments
        )
        return events

    async def _relationship_events(self, document_id: UUID | None) -> list[HistoryEvent]:
        statement = select(DocumentRelationship)
        if document_id is not None:
            statement = statement.where(
                or_(
                    DocumentRelationship.source_document_id == document_id,
                    DocumentRelationship.target_document_id == document_id,
                )
            )
        relationships = list((await self._session.execute(statement)).scalars())
        return [
            HistoryEvent(
                id=relationship.id,
                type="document_relationship_decision",
                document_id=relationship.source_document_id,
                actor_id=relationship.decided_by_id,
                occurred_at=relationship.decided_at,
                reason=relationship.reason,
                before={"status": "candidate"},
                after={"status": relationship.status},
                source_id=relationship.id,
            )
            for relationship in relationships
            if relationship.decided_at is not None
        ]

    async def _impact_events(self, document_id: UUID | None) -> list[HistoryEvent]:
        statement = select(DocumentImpact)
        if document_id is not None:
            statement = statement.where(
                or_(
                    DocumentImpact.source_document_id == document_id,
                    DocumentImpact.target_document_id == document_id,
                )
            )
        impacts = list((await self._session.execute(statement)).scalars())
        events = [
            HistoryEvent(
                id=impact.id,
                type="document_impact_decision",
                document_id=impact.source_document_id,
                actor_id=impact.decided_by_id,
                occurred_at=impact.decided_at,
                reason=impact.reason,
                before={"status": "candidate"},
                after={"status": impact.status},
                source_id=impact.id,
            )
            for impact in impacts
            if impact.decided_at is not None
        ]
        events.extend(
            HistoryEvent(
                id=impact.id,
                type="document_impact_modification_decision",
                document_id=impact.source_document_id,
                actor_id=impact.modification_decided_by_id,
                occurred_at=impact.modification_decided_at,
                reason=impact.reason,
                before=None,
                after={"modification_required": impact.modification_required},
                source_id=impact.id,
            )
            for impact in impacts
            if impact.modification_decided_at is not None
        )
        return events

    async def _evidence_events(self, document_id: UUID | None) -> list[HistoryEvent]:
        statement = select(DocumentEvidenceLink)
        if document_id is not None:
            statement = statement.where(DocumentEvidenceLink.document_id == document_id)
        links = list((await self._session.execute(statement)).scalars())
        events = [
            HistoryEvent(
                id=link.id,
                type="evidence_decision",
                document_id=link.document_id,
                actor_id=link.decided_by_id,
                occurred_at=link.decided_at,
                reason=link.reason,
                before={"status": "candidate"},
                after={"status": link.status},
                source_id=link.id,
            )
            for link in links
            if link.decided_at is not None
        ]
        events.extend(
            HistoryEvent(
                id=link.id,
                type="evidence_stale",
                document_id=link.document_id,
                actor_id=link.decided_by_id,
                occurred_at=link.decided_at or link.created_at,
                reason=link.reason,
                before={"freshness": "current"},
                after={"freshness": link.freshness},
                source_id=link.id,
            )
            for link in links
            if link.freshness == "stale"
        )
        events.extend(
            HistoryEvent(
                id=link.id,
                type="evidence_review",
                document_id=link.document_id,
                actor_id=link.reviewed_by_id,
                occurred_at=link.reviewed_at,
                reason=link.reason,
                before=None,
                after={"freshness": link.freshness},
                source_id=link.id,
            )
            for link in links
            if link.reviewed_at is not None
        )
        return events

    async def _approval_events(self, document_id: UUID | None) -> list[HistoryEvent]:
        statement = select(ApprovalWorkflowAudit, ApprovalWorkflow.document_id).join(
            ApprovalWorkflow, ApprovalWorkflowAudit.workflow_id == ApprovalWorkflow.id
        )
        if document_id is not None:
            statement = statement.where(ApprovalWorkflow.document_id == document_id)
        rows = (await self._session.execute(statement)).all()
        return [
            HistoryEvent(
                id=audit.id,
                type="approval_audit",
                document_id=workflow_document_id,
                actor_id=audit.actor_id,
                occurred_at=audit.changed_at,
                reason=audit.reason,
                before=_safe_audit_data(audit.before_json),
                after=_safe_audit_data(audit.after_json),
                source_id=audit.id,
            )
            for audit, workflow_document_id in rows
        ]

    async def _format_events(self, document_id: UUID | None) -> list[HistoryEvent]:
        statement = select(
            FormatCheck, ExternalEditResult.document_id, ExternalEditResult.created_by_id
        ).join(ExternalEditResult, FormatCheck.external_edit_result_id == ExternalEditResult.id)
        if document_id is not None:
            statement = statement.where(ExternalEditResult.document_id == document_id)
        rows = (await self._session.execute(statement)).all()
        events: list[HistoryEvent] = []
        for check, result_document_id, creator_id in rows:
            events.append(
                HistoryEvent(
                    id=check.id,
                    type="format_check",
                    document_id=result_document_id,
                    actor_id=creator_id,
                    occurred_at=check.created_at,
                    reason=None,
                    before=None,
                    after={"automatic_check_completed": check.automatic_check_completed},
                    source_id=check.id,
                )
            )
            if check.automatic_check_completed:
                events.append(
                    HistoryEvent(
                        id=check.id,
                        type="format_check_completed",
                        document_id=result_document_id,
                        actor_id=creator_id,
                        occurred_at=check.updated_at,
                        reason=None,
                        before={"automatic_check_completed": False},
                        after={"automatic_check_completed": True},
                        source_id=check.id,
                    )
                )
            if check.visual_review != "pending":
                events.append(
                    HistoryEvent(
                        id=check.id,
                        type="visual_review",
                        document_id=result_document_id,
                        actor_id=creator_id,
                        occurred_at=check.updated_at,
                        reason=None,
                        before={"visual_review": "pending"},
                        after={"visual_review": check.visual_review},
                        source_id=check.id,
                    )
                )
        return events

    async def _completion_events(self, document_id: UUID | None) -> list[HistoryEvent]:
        statement = select(DocumentCompletion)
        if document_id is not None:
            statement = statement.where(DocumentCompletion.document_id == document_id)
        completions = list((await self._session.execute(statement)).scalars())
        return [
            HistoryEvent(
                id=completion.id,
                type="document_completion",
                document_id=completion.document_id,
                actor_id=completion.completed_by_id,
                occurred_at=completion.completed_at,
                reason=None,
                before=None,
                after={"original_format": completion.original_format},
                source_id=completion.id,
            )
            for completion in completions
        ]
