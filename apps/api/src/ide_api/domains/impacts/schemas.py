from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RelationshipType(StrEnum):
    HIERARCHY = "hierarchy"
    SEMANTIC = "semantic"
    CITATION = "citation"
    SCREENSHOT = "screenshot"


class CandidateStatus(StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class DocumentRelationshipCandidateCreate(BaseModel):
    source_document_id: UUID
    source_location: str = Field(min_length=1)
    target_document_id: UUID
    target_location: str = Field(min_length=1)
    relationship_type: RelationshipType
    reason: str = Field(min_length=1)


class DocumentImpactCandidateCreate(BaseModel):
    source_document_id: UUID
    source_location: str = Field(min_length=1)
    target_document_id: UUID
    target_location: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    proposed_modification: str = Field(min_length=1)


class DocumentRelationshipCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_document_id: UUID
    source_location: str
    target_document_id: UUID
    target_location: str
    relationship_type: RelationshipType
    reason: str
    status: CandidateStatus
    created_at: datetime
    decided_at: datetime | None
    decided_by_id: UUID | None


class DocumentImpactCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_document_id: UUID
    source_location: str
    target_document_id: UUID
    target_location: str
    reason: str
    proposed_modification: str
    status: CandidateStatus
    modification_required: bool | None
    created_at: datetime
    decided_at: datetime | None
    decided_by_id: UUID | None
    modification_decided_at: datetime | None
    modification_decided_by_id: UUID | None


class DocumentCandidatesResponse(BaseModel):
    document_id: UUID
    relationships: list[DocumentRelationshipCandidateResponse] = Field(default_factory=list)
    impacts: list[DocumentImpactCandidateResponse] = Field(default_factory=list)
