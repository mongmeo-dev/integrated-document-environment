from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.domains.completion.models import DocumentCompletion
from ide_api.domains.completion.repository import CompletionRepository
from ide_api.domains.completion.schemas import (
    CompletionBlockingCode,
    CompletionBlockingReason,
    CompletionEvaluation,
)


class CompletionBlockedError(Exception):
    def __init__(self, evaluation: CompletionEvaluation) -> None:
        self.evaluation = evaluation
        super().__init__("Document completion is blocked.")


class CompletionAlreadyExistsError(Exception):
    pass


class CompletionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = CompletionRepository(session)

    async def evaluate(self, *, document_id: UUID, latex_revision_id: UUID) -> CompletionEvaluation:
        reasons: list[CompletionBlockingReason] = []
        if not await self._repository.document_exists(document_id):
            self._add(reasons, CompletionBlockingCode.DOCUMENT_NOT_FOUND)
            return CompletionEvaluation(
                document_id=document_id,
                latex_revision_id=latex_revision_id,
                blocking_reasons=reasons,
            )

        revision = await self._repository.get_latex_revision(latex_revision_id)
        if revision is None:
            self._add(reasons, CompletionBlockingCode.LATEX_REVISION_NOT_FOUND)
        elif revision.document_id != document_id:
            self._add(reasons, CompletionBlockingCode.LATEX_REVISION_DOCUMENT_MISMATCH)
        else:
            latest_revision = await self._repository.get_latest_latex_revision(document_id)
            if latest_revision is None:
                self._add(reasons, CompletionBlockingCode.LATEX_PROJECT_MISSING)
            elif latest_revision.id != revision.id:
                self._add(reasons, CompletionBlockingCode.LATEX_REVISION_NOT_LATEST)
            if revision.compile_status == "pending":
                self._add(reasons, CompletionBlockingCode.COMPILE_INCOMPLETE)
            elif revision.compile_status == "failed":
                self._add(reasons, CompletionBlockingCode.COMPILE_FAILED)
            elif revision.compiled_pdf_object_key is None or revision.compiled_pdf_sha256 is None:
                self._add(reasons, CompletionBlockingCode.COMPILED_PDF_MISSING)
            if revision.conversion_status == "pending_review":
                self._add(reasons, CompletionBlockingCode.CONVERSION_REVIEW_PENDING)
            elif revision.conversion_status == "rejected":
                self._add(reasons, CompletionBlockingCode.CONVERSION_REJECTED)

        counts = await self._repository.get_gate_counts(document_id)
        self._add_count(
            reasons, CompletionBlockingCode.PENDING_CHANGE_REQUESTS, counts.pending_change_requests
        )
        self._add_count(
            reasons,
            CompletionBlockingCode.PENDING_CHANGE_PROPOSALS,
            counts.pending_change_proposals,
        )
        self._add_count(
            reasons,
            CompletionBlockingCode.PENDING_RELATIONSHIP_CANDIDATES,
            counts.pending_relationship_candidates,
        )
        self._add_count(
            reasons,
            CompletionBlockingCode.PENDING_RELATIONSHIP_ANALYSES,
            counts.pending_relationship_analyses,
        )
        self._add_count(
            reasons,
            CompletionBlockingCode.PENDING_IMPACT_CANDIDATES,
            counts.pending_impact_candidates,
        )
        self._add_count(
            reasons,
            CompletionBlockingCode.PENDING_EVIDENCE_CANDIDATES,
            counts.pending_evidence_candidates,
        )
        self._add_count(reasons, CompletionBlockingCode.STALE_EVIDENCE, counts.stale_evidence)
        if counts.approval_workflows == 0:
            self._add(reasons, CompletionBlockingCode.APPROVAL_WORKFLOW_MISSING)
        else:
            self._add_count(
                reasons,
                CompletionBlockingCode.APPROVAL_STEPS_INCOMPLETE,
                max(
                    1 if counts.approval_steps == 0 else 0,
                    counts.incomplete_approval_steps,
                    counts.incomplete_approval_workflows,
                ),
            )
        if await self._repository.get_completion(document_id) is not None:
            self._add(reasons, CompletionBlockingCode.DOCUMENT_ALREADY_COMPLETED)

        return CompletionEvaluation(
            document_id=document_id,
            latex_revision_id=latex_revision_id,
            blocking_reasons=reasons,
        )

    async def complete(
        self,
        *,
        document_id: UUID,
        latex_revision_id: UUID,
        completed_by_id: UUID,
    ) -> DocumentCompletion:
        evaluation = await self.evaluate(
            document_id=document_id,
            latex_revision_id=latex_revision_id,
        )
        if not evaluation.is_complete_allowed:
            raise CompletionBlockedError(evaluation)

        revision = await self._repository.get_latex_revision(latex_revision_id)
        if (
            revision is None
            or revision.document_id != document_id
            or revision.compile_status != "succeeded"
            or revision.compiled_pdf_object_key is None
            or revision.compiled_pdf_sha256 is None
        ):
            raise CompletionBlockedError(
                CompletionEvaluation(
                    document_id=document_id,
                    latex_revision_id=latex_revision_id,
                    blocking_reasons=[
                        CompletionBlockingReason(
                            code=CompletionBlockingCode.LATEX_REVISION_NOT_FOUND,
                            count=1,
                        )
                    ],
                )
            )
        completion = DocumentCompletion(
            document_id=document_id,
            latex_revision_id=latex_revision_id,
            compiled_pdf_sha256=revision.compiled_pdf_sha256,
            completed_by_id=completed_by_id,
        )
        self._repository.add(completion)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise CompletionAlreadyExistsError from error
        return completion

    @staticmethod
    def _add(reasons: list[CompletionBlockingReason], code: CompletionBlockingCode) -> None:
        reasons.append(CompletionBlockingReason(code=code, count=1))

    @staticmethod
    def _add_count(
        reasons: list[CompletionBlockingReason], code: CompletionBlockingCode, count: int
    ) -> None:
        if count > 0:
            reasons.append(CompletionBlockingReason(code=code, count=count))
