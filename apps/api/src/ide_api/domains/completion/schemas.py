from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompletionBlockingCode(StrEnum):
    DOCUMENT_NOT_FOUND = "document_not_found"
    LATEX_PROJECT_MISSING = "latex_project_missing"
    LATEX_REVISION_NOT_FOUND = "latex_revision_not_found"
    LATEX_REVISION_DOCUMENT_MISMATCH = "latex_revision_document_mismatch"
    LATEX_REVISION_NOT_LATEST = "latex_revision_not_latest"
    COMPILE_INCOMPLETE = "compile_incomplete"
    COMPILE_FAILED = "compile_failed"
    COMPILED_PDF_MISSING = "compiled_pdf_missing"
    CONVERSION_REVIEW_PENDING = "conversion_review_pending"
    CONVERSION_REJECTED = "conversion_rejected"
    PENDING_CHANGE_REQUESTS = "pending_change_requests"
    PENDING_CHANGE_PROPOSALS = "pending_change_proposals"
    PENDING_RELATIONSHIP_CANDIDATES = "pending_relationship_candidates"
    PENDING_RELATIONSHIP_ANALYSES = "pending_relationship_analyses"
    PENDING_IMPACT_CANDIDATES = "pending_impact_candidates"
    PENDING_EVIDENCE_CANDIDATES = "pending_evidence_candidates"
    STALE_EVIDENCE = "stale_evidence"
    APPROVAL_WORKFLOW_MISSING = "approval_workflow_missing"
    APPROVAL_STEPS_INCOMPLETE = "approval_steps_incomplete"
    DOCUMENT_ALREADY_COMPLETED = "document_already_completed"


class CompletionBlockingReason(BaseModel):
    code: CompletionBlockingCode
    count: int = Field(ge=1)


class CompletionRequest(BaseModel):
    document_id: UUID
    latex_revision_id: UUID


class CompletionEvaluation(BaseModel):
    document_id: UUID
    latex_revision_id: UUID
    blocking_reasons: list[CompletionBlockingReason] = Field(default_factory=list)

    @property
    def is_complete_allowed(self) -> bool:
        return not self.blocking_reasons


class DocumentCompletionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    latex_revision_id: UUID
    compiled_pdf_sha256: str
    completed_by_id: UUID
    completed_at: datetime
