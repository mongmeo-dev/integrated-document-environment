from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(StrEnum):
    QUEUED = "queued"
    VALIDATING = "validating"
    READY = "ready"
    REJECTED = "rejected"


class InputKind(StrEnum):
    LATEX_PROJECT = "latex_project"
    DOCX_IMPORT = "docx_import"
    TEXT_PDF = "text_pdf"
    SCANNED_PDF = "scanned_pdf"


class OriginalFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    media_type: str
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DocumentCapabilities(BaseModel):
    analysis: bool
    source_editing: bool
    compilation: bool
    conversion_review: bool
    approved_output: bool


class DocumentRejection(BaseModel):
    code: str
    message: str


class DocumentCreator(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str


class DocumentResponse(BaseModel):
    id: UUID
    original_file: OriginalFileResponse
    status: DocumentStatus
    input_kind: InputKind | None
    capabilities: DocumentCapabilities
    rejection: DocumentRejection | None
    creator: DocumentCreator
    created_at: datetime
