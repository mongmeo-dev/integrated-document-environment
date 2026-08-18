from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompletionBlockingCode(StrEnum):
    DOCUMENT_NOT_FOUND = "document_not_found"
    EXTERNAL_EDIT_RESULT_NOT_FOUND = "external_edit_result_not_found"
    EXTERNAL_EDIT_RESULT_DOCUMENT_MISMATCH = "external_edit_result_document_mismatch"
    SCANNED_PDF = "scanned_pdf"
    UNSUPPORTED_ORIGINAL_FORMAT = "unsupported_original_format"
    CROSS_FORMAT_RESULT = "cross_format_result"
    FORMAT_RESULT_NOT_PASSED = "format_result_not_passed"
    AUTOMATIC_CHECK_INCOMPLETE = "automatic_check_incomplete"
    VISUAL_REVIEW_INCOMPLETE = "visual_review_incomplete"
    UNRESOLVED_FORMAT_DIFFERENCES = "unresolved_format_differences"
    PENDING_CHANGE_REQUESTS = "pending_change_requests"
    PENDING_CHANGE_PROPOSALS = "pending_change_proposals"
    PENDING_RELATIONSHIP_CANDIDATES = "pending_relationship_candidates"
    PENDING_IMPACT_CANDIDATES = "pending_impact_candidates"
    PENDING_EVIDENCE_CANDIDATES = "pending_evidence_candidates"
    STALE_EVIDENCE = "stale_evidence"
    APPROVAL_WORKFLOW_MISSING = "approval_workflow_missing"
    APPROVAL_STEPS_INCOMPLETE = "approval_steps_incomplete"
    DOCUMENT_ALREADY_COMPLETED = "document_already_completed"


class CompletionBlockingReason(BaseModel):
    code: CompletionBlockingCode
    count: int = Field(ge=1)


class CompletionEvaluation(BaseModel):
    document_id: UUID
    external_edit_result_id: UUID
    blocking_reasons: list[CompletionBlockingReason] = Field(default_factory=list)

    @property
    def is_complete_allowed(self) -> bool:
        return not self.blocking_reasons


class DocumentCompletionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    external_edit_result_id: UUID
    original_format: str
    completed_by_id: UUID
    completed_at: datetime
