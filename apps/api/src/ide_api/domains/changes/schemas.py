from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChangeRequestStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class ChangeProposalStatus(StrEnum):
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class ChangeCommentStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"


class ChangeRequestCreate(BaseModel):
    document_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    assignee_id: UUID | None = None


class ChangeProposalCreate(BaseModel):
    proposed_text: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class ChangeCommentCreate(BaseModel):
    body: str = Field(min_length=1)
    assignee_id: UUID | None = None

    @field_validator("body")
    @classmethod
    def body_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Body must not be blank.")
        return value


class ChangeProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    change_request_id: UUID
    proposed_text: str
    rationale: str
    status: ChangeProposalStatus
    created_at: datetime
    decided_at: datetime | None
    decided_by_id: UUID | None


class ChangeCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    change_request_id: UUID
    author_id: UUID
    assignee_id: UUID | None
    body: str
    status: ChangeCommentStatus
    created_at: datetime
    resolved_at: datetime | None
    resolved_by_id: UUID | None


class ChangeRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    requester_id: UUID
    title: str
    description: str
    status: ChangeRequestStatus
    assignee_id: UUID | None
    created_at: datetime
    updated_at: datetime
    proposals: list[ChangeProposalResponse] = Field(default_factory=list)
    comments: list[ChangeCommentResponse] = Field(default_factory=list)
