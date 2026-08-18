from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvidenceType(StrEnum):
    UPLOAD = "upload"
    DESCRIPTION = "description"
    APP_SNAPSHOT = "app_snapshot"
    WEB_SNAPSHOT = "web_snapshot"
    SERVER_CODE = "server_code"
    DATABASE = "database"
    CLOUD_CONFIG = "cloud_config"
    TEST_RESULT = "test_result"


class EvidenceLinkStatus(StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class EvidenceFreshness(StrEnum):
    CURRENT = "current"
    STALE = "stale"


class EvidenceItemCreate(BaseModel):
    evidence_type: EvidenceType
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    reference: str | None = None
    location: str | None = None
    version: str | None = Field(default=None, max_length=255)


class EvidenceItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    reference: str | None = None
    location: str | None = None
    version: str | None = Field(default=None, max_length=255)


class EvidenceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evidence_type: EvidenceType
    title: str
    description: str
    reference: str | None
    location: str | None
    version: str | None
    created_at: datetime
    updated_at: datetime


class DocumentEvidenceLinkCreate(BaseModel):
    document_id: UUID
    evidence_id: UUID
    reason: str = Field(min_length=1)


class DocumentEvidenceLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    evidence_id: UUID
    status: EvidenceLinkStatus
    freshness: EvidenceFreshness
    reason: str
    created_at: datetime
    decided_by_id: UUID | None
    decided_at: datetime | None
    reviewed_by_id: UUID | None
    reviewed_at: datetime | None
