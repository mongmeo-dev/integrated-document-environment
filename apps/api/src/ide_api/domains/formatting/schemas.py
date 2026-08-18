from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OriginalFormat(StrEnum):
    DOCX = "docx"
    PDF = "pdf"


class ExternalEditResultStatus(StrEnum):
    UPLOADED = "uploaded"
    CHECKING = "checking"
    NEEDS_REVISION = "needs_revision"
    PASSED = "passed"


class VisualReviewStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class FormatDifferenceCategory(StrEnum):
    FONT = "font"
    COLOR = "color"
    TABLE = "table"
    MARGIN = "margin"
    LINE_SPACING = "line_spacing"
    FONT_SIZE = "font_size"
    OTHER = "other"


class ExternalEditResultCreate(BaseModel):
    document_id: UUID
    document_version_id: UUID
    original_format: OriginalFormat
    original_filename: str = Field(min_length=1, max_length=255)
    media_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    object_key: str = Field(min_length=1, max_length=1024)


class DetectedFormatDifference(BaseModel):
    category: FormatDifferenceCategory
    location: str = Field(min_length=1)
    original_value: str
    proposed_value: str


class FormatDifferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    format_check_id: UUID
    category: FormatDifferenceCategory
    location: str
    original_value: str
    proposed_value: str
    resolved: bool
    created_at: datetime


class FormatCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_edit_result_id: UUID
    automatic_check_completed: bool
    visual_review: VisualReviewStatus
    unresolved_difference_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    differences: list[FormatDifferenceResponse] = Field(default_factory=list)


class ExternalEditResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    document_version_id: UUID
    original_format: OriginalFormat
    original_filename: str
    media_type: str
    size_bytes: int = Field(ge=0)
    sha256: str
    object_key: str
    status: ExternalEditResultStatus
    created_by_id: UUID
    created_at: datetime
    format_check: FormatCheckResponse
