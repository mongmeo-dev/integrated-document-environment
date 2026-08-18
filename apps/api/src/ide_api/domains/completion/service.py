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
from ide_api.domains.formatting.models import FormatCheck


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

    async def evaluate(
        self, *, document_id: UUID, external_edit_result_id: UUID
    ) -> CompletionEvaluation:
        reasons: list[CompletionBlockingReason] = []
        if not await self._repository.document_exists(document_id):
            self._add(reasons, CompletionBlockingCode.DOCUMENT_NOT_FOUND)
            return CompletionEvaluation(
                document_id=document_id,
                external_edit_result_id=external_edit_result_id,
                blocking_reasons=reasons,
            )

        external_result = await self._repository.get_external_result(external_edit_result_id)
        if external_result is None:
            self._add(reasons, CompletionBlockingCode.EXTERNAL_EDIT_RESULT_NOT_FOUND)
        else:
            result, version, check = external_result
            if result.document_id != document_id or version.document_id != document_id:
                self._add(reasons, CompletionBlockingCode.EXTERNAL_EDIT_RESULT_DOCUMENT_MISMATCH)
            self._evaluate_format(
                reasons, result.status, result.original_format, version.input_kind, check
            )

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
            external_edit_result_id=external_edit_result_id,
            blocking_reasons=reasons,
        )

    async def complete(
        self,
        *,
        document_id: UUID,
        external_edit_result_id: UUID,
        completed_by_id: UUID,
    ) -> DocumentCompletion:
        evaluation = await self.evaluate(
            document_id=document_id,
            external_edit_result_id=external_edit_result_id,
        )
        if not evaluation.is_complete_allowed:
            raise CompletionBlockedError(evaluation)

        external_result = await self._repository.get_external_result(external_edit_result_id)
        if external_result is None:
            raise CompletionBlockedError(
                CompletionEvaluation(
                    document_id=document_id,
                    external_edit_result_id=external_edit_result_id,
                    blocking_reasons=[
                        CompletionBlockingReason(
                            code=CompletionBlockingCode.EXTERNAL_EDIT_RESULT_NOT_FOUND,
                            count=1,
                        )
                    ],
                )
            )
        result, _, _ = external_result
        completion = DocumentCompletion(
            document_id=document_id,
            external_edit_result_id=external_edit_result_id,
            original_format=result.original_format,
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
    def _evaluate_format(
        reasons: list[CompletionBlockingReason],
        result_status: str,
        result_format: str,
        input_kind: str | None,
        check: FormatCheck | None,
    ) -> None:
        if input_kind == "scanned_pdf":
            CompletionService._add(reasons, CompletionBlockingCode.SCANNED_PDF)
            return
        expected_format = {"editable_docx": "docx", "text_pdf": "pdf"}.get(input_kind)
        if expected_format is None:
            CompletionService._add(reasons, CompletionBlockingCode.UNSUPPORTED_ORIGINAL_FORMAT)
            return
        if result_format != expected_format:
            CompletionService._add(reasons, CompletionBlockingCode.CROSS_FORMAT_RESULT)
        if result_status != "passed":
            CompletionService._add(reasons, CompletionBlockingCode.FORMAT_RESULT_NOT_PASSED)
        if check is None:
            CompletionService._add(reasons, CompletionBlockingCode.AUTOMATIC_CHECK_INCOMPLETE)
            CompletionService._add(reasons, CompletionBlockingCode.VISUAL_REVIEW_INCOMPLETE)
            return
        if not check.automatic_check_completed:
            CompletionService._add(reasons, CompletionBlockingCode.AUTOMATIC_CHECK_INCOMPLETE)
        if check.visual_review != "passed":
            CompletionService._add(reasons, CompletionBlockingCode.VISUAL_REVIEW_INCOMPLETE)
        if check.unresolved_difference_count > 0:
            CompletionService._add(
                reasons,
                CompletionBlockingCode.UNRESOLVED_FORMAT_DIFFERENCES,
                check.unresolved_difference_count,
            )

    @staticmethod
    def _add(reasons: list[CompletionBlockingReason], code: CompletionBlockingCode) -> None:
        reasons.append(CompletionBlockingReason(code=code, count=1))

    @staticmethod
    def _add_count(
        reasons: list[CompletionBlockingReason], code: CompletionBlockingCode, count: int
    ) -> None:
        if count > 0:
            reasons.append(CompletionBlockingReason(code=code, count=count))
