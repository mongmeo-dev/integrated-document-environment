from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class RevisionOrigin(StrEnum):
    LATEX_UPLOAD = "latex_upload"
    DOCX_CONVERSION = "docx_conversion"
    WEB_EDIT = "web_edit"


class ConversionStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class CompileStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ConversionDecision(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class LatexProjectResponse(BaseModel):
    revision_id: UUID
    document_id: UUID
    entrypoint: str
    source: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    files: list[str]
    origin: RevisionOrigin
    conversion_status: ConversionStatus
    compile_status: CompileStatus
    compile_log: str | None
    compiled_pdf_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    preview_available: bool
    created_at: datetime


class LatexSourceRevisionCreate(BaseModel):
    expected_revision_id: UUID
    source: str = Field(min_length=1, max_length=2_000_000)


class ConversionReviewCreate(BaseModel):
    expected_revision_id: UUID
    decision: ConversionDecision
    reason: str = Field(min_length=1, max_length=4000)
