from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    CURRENT = "current"
    COMPLETED = "completed"


class ApprovalStepCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    assignee_id: UUID
    sequence: int = Field(ge=1)


class ApprovalWorkflowCreate(BaseModel):
    document_id: UUID
    steps: list[ApprovalStepCreate] = Field(min_length=1)


class ApprovalStepUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    assignee_id: UUID | None = None
    sequence: int | None = Field(default=None, ge=1)
    reason: str | None = Field(default=None, min_length=1)


class ApprovalStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    name: str
    assignee_id: UUID
    sequence: int
    status: ApprovalStatus
    completed_at: datetime | None


class ApprovalWorkflowAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    actor_id: UUID
    reason: str
    changed_at: datetime
    before_json: dict
    after_json: dict


class ApprovalWorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    status: ApprovalStatus
    is_started: bool
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    steps: list[ApprovalStepResponse] = Field(default_factory=list)
