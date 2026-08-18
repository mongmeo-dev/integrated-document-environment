from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ide_api.domains.approvals.models import ApprovalStep, ApprovalWorkflow, ApprovalWorkflowAudit


class ApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, item: ApprovalWorkflow | ApprovalStep | ApprovalWorkflowAudit) -> None:
        self._session.add(item)

    async def get_workflow_by_id(self, workflow_id: UUID) -> ApprovalWorkflow | None:
        result = await self._session.execute(
            select(ApprovalWorkflow)
            .options(selectinload(ApprovalWorkflow.steps))
            .where(ApprovalWorkflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def get_workflow_by_document_id(self, document_id: UUID) -> ApprovalWorkflow | None:
        result = await self._session.execute(
            select(ApprovalWorkflow)
            .options(selectinload(ApprovalWorkflow.steps))
            .where(ApprovalWorkflow.document_id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_step_by_id(self, step_id: UUID) -> ApprovalStep | None:
        result = await self._session.execute(
            select(ApprovalStep)
            .options(selectinload(ApprovalStep.workflow).selectinload(ApprovalWorkflow.steps))
            .where(ApprovalStep.id == step_id)
        )
        return result.scalar_one_or_none()

    async def list_audits_by_workflow_id(self, workflow_id: UUID) -> list[ApprovalWorkflowAudit]:
        result = await self._session.execute(
            select(ApprovalWorkflowAudit)
            .where(ApprovalWorkflowAudit.workflow_id == workflow_id)
            .order_by(ApprovalWorkflowAudit.changed_at)
        )
        return list(result.scalars())
