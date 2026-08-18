from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.domains.approvals.models import ApprovalStep, ApprovalWorkflow, ApprovalWorkflowAudit
from ide_api.domains.approvals.repository import ApprovalRepository
from ide_api.domains.approvals.schemas import (
    ApprovalStatus,
    ApprovalStepCreate,
    ApprovalStepUpdate,
    ApprovalWorkflowCreate,
)


class ApprovalWorkflowNotFoundError(Exception):
    pass


class ApprovalStepNotFoundError(Exception):
    pass


class ApprovalWorkflowAlreadyExistsError(Exception):
    pass


class InvalidApprovalWorkflowError(Exception):
    pass


class ApprovalStepImmutableError(Exception):
    pass


class ApprovalStepSequenceError(Exception):
    pass


class ApprovalNotAuthorizedError(Exception):
    pass


class InvalidApprovalTransitionError(Exception):
    pass


class ApprovalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = ApprovalRepository(session)

    async def create_workflow(self, *, data: ApprovalWorkflowCreate) -> ApprovalWorkflow:
        if await self._repository.get_workflow_by_document_id(data.document_id) is not None:
            raise ApprovalWorkflowAlreadyExistsError
        self._validate_sequences([step.sequence for step in data.steps])

        workflow = ApprovalWorkflow(
            document_id=data.document_id,
            status=ApprovalStatus.PENDING.value,
            is_started=False,
            steps=[
                ApprovalStep(
                    name=step.name,
                    assignee_id=step.assignee_id,
                    sequence=step.sequence,
                    status=ApprovalStatus.PENDING.value,
                )
                for step in data.steps
            ],
        )
        self._repository.add(workflow)
        await self._session.commit()
        return workflow

    async def get_workflow(self, *, workflow_id: UUID) -> ApprovalWorkflow:
        return await self._get_workflow(workflow_id)

    async def get_workflow_for_document(self, *, document_id: UUID) -> ApprovalWorkflow:
        workflow = await self._repository.get_workflow_by_document_id(document_id)
        if workflow is None:
            raise ApprovalWorkflowNotFoundError
        return workflow

    async def list_workflow_audits(self, *, workflow_id: UUID) -> list[ApprovalWorkflowAudit]:
        await self._get_workflow(workflow_id)
        return await self._repository.list_audits_by_workflow_id(workflow_id)

    async def start_workflow(self, *, workflow_id: UUID) -> ApprovalWorkflow:
        workflow = await self._get_workflow(workflow_id)
        if workflow.is_started or ApprovalStatus(workflow.status) is not ApprovalStatus.PENDING:
            raise InvalidApprovalTransitionError
        if not workflow.steps:
            raise InvalidApprovalWorkflowError

        current_step = min(workflow.steps, key=lambda step: step.sequence)
        workflow.is_started = True
        workflow.started_at = datetime.now(UTC)
        workflow.status = ApprovalStatus.CURRENT.value
        current_step.status = ApprovalStatus.CURRENT.value
        await self._session.commit()
        return workflow

    async def add_approval_step(
        self,
        *,
        workflow_id: UUID,
        data: ApprovalStepCreate,
        actor_id: UUID,
        reason: str,
    ) -> ApprovalStep:
        workflow = await self._get_workflow(workflow_id)
        if ApprovalStatus(workflow.status) is ApprovalStatus.COMPLETED:
            raise InvalidApprovalTransitionError
        self._validate_sequence_for_workflow(workflow, data.sequence)

        before = self._workflow_snapshot(workflow)
        step = ApprovalStep(
            workflow_id=workflow.id,
            name=data.name,
            assignee_id=data.assignee_id,
            sequence=data.sequence,
            status=ApprovalStatus.PENDING.value,
        )
        self._repository.add(step)
        workflow.steps.append(step)
        if workflow.is_started:
            await self._session.flush()
            self._record_audit(
                workflow=workflow,
                actor_id=actor_id,
                reason=reason,
                before=before,
                after=self._workflow_snapshot(workflow),
            )
        await self._session.commit()
        return step

    async def update_approval_step(
        self, *, step_id: UUID, data: ApprovalStepUpdate, actor_id: UUID
    ) -> ApprovalStep:
        step = await self._get_step(step_id)
        workflow = step.workflow
        if ApprovalStatus(step.status) is ApprovalStatus.COMPLETED:
            raise ApprovalStepImmutableError
        if ApprovalStatus(workflow.status) is ApprovalStatus.COMPLETED:
            raise InvalidApprovalTransitionError

        changes = data.model_dump(exclude_unset=True, exclude={"reason"})
        if "sequence" in changes:
            self._validate_sequence_for_workflow(
                workflow, changes["sequence"], exclude_step_id=step.id
            )
        if not changes:
            return step

        before = self._workflow_snapshot(workflow)
        for field, value in changes.items():
            setattr(step, field, value)
        if workflow.is_started:
            if data.reason is None:
                raise InvalidApprovalWorkflowError
            self._record_audit(
                workflow=workflow,
                actor_id=actor_id,
                reason=data.reason,
                before=before,
                after=self._workflow_snapshot(workflow),
            )
        await self._session.commit()
        return step

    async def approve_step(self, *, step_id: UUID, actor_id: UUID) -> ApprovalWorkflow:
        step = await self._get_step(step_id)
        workflow = step.workflow
        if not workflow.is_started or ApprovalStatus(workflow.status) is not ApprovalStatus.CURRENT:
            raise InvalidApprovalTransitionError
        if ApprovalStatus(step.status) is not ApprovalStatus.CURRENT:
            raise InvalidApprovalTransitionError
        if step.assignee_id != actor_id:
            raise ApprovalNotAuthorizedError

        step.status = ApprovalStatus.COMPLETED.value
        step.completed_at = datetime.now(UTC)
        next_step = min(
            (
                candidate
                for candidate in workflow.steps
                if candidate.status == ApprovalStatus.PENDING.value
            ),
            key=lambda candidate: candidate.sequence,
            default=None,
        )
        if next_step is None:
            workflow.status = ApprovalStatus.COMPLETED.value
            workflow.completed_at = datetime.now(UTC)
        else:
            next_step.status = ApprovalStatus.CURRENT.value
        await self._session.commit()
        return workflow

    async def _get_workflow(self, workflow_id: UUID) -> ApprovalWorkflow:
        workflow = await self._repository.get_workflow_by_id(workflow_id)
        if workflow is None:
            raise ApprovalWorkflowNotFoundError
        return workflow

    async def _get_step(self, step_id: UUID) -> ApprovalStep:
        step = await self._repository.get_step_by_id(step_id)
        if step is None:
            raise ApprovalStepNotFoundError
        return step

    @staticmethod
    def _validate_sequences(sequences: list[int]) -> None:
        if len(sequences) != len(set(sequences)):
            raise ApprovalStepSequenceError

    def _validate_sequence_for_workflow(
        self, workflow: ApprovalWorkflow, sequence: int, exclude_step_id: UUID | None = None
    ) -> None:
        if any(step.sequence == sequence and step.id != exclude_step_id for step in workflow.steps):
            raise ApprovalStepSequenceError
        completed_sequences = [
            step.sequence
            for step in workflow.steps
            if ApprovalStatus(step.status) is ApprovalStatus.COMPLETED
        ]
        if completed_sequences and sequence <= max(completed_sequences):
            raise ApprovalStepSequenceError
        current_step = next(
            (
                step
                for step in workflow.steps
                if ApprovalStatus(step.status) is ApprovalStatus.CURRENT
            ),
            None,
        )
        if current_step is None:
            return
        if current_step.id == exclude_step_id:
            pending_sequences = [
                step.sequence
                for step in workflow.steps
                if ApprovalStatus(step.status) is ApprovalStatus.PENDING
            ]
            if pending_sequences and sequence >= min(pending_sequences):
                raise ApprovalStepSequenceError
        elif sequence <= current_step.sequence:
            raise ApprovalStepSequenceError

    def _record_audit(
        self,
        *,
        workflow: ApprovalWorkflow,
        actor_id: UUID,
        reason: str,
        before: dict,
        after: dict,
    ) -> None:
        self._repository.add(
            ApprovalWorkflowAudit(
                workflow_id=workflow.id,
                actor_id=actor_id,
                reason=reason,
                before_json=before,
                after_json=after,
            )
        )

    @staticmethod
    def _workflow_snapshot(workflow: ApprovalWorkflow) -> dict:
        return {
            "id": str(workflow.id),
            "document_id": str(workflow.document_id),
            "status": workflow.status,
            "is_started": workflow.is_started,
            "steps": [
                {
                    "id": str(step.id),
                    "name": step.name,
                    "assignee_id": str(step.assignee_id),
                    "sequence": step.sequence,
                    "status": step.status,
                }
                for step in sorted(workflow.steps, key=lambda candidate: candidate.sequence)
            ],
        }
