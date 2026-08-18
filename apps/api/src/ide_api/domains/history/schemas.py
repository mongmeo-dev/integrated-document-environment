from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class HistoryEvent(BaseModel):
    id: UUID
    type: str
    document_id: UUID
    actor_id: UUID | None
    occurred_at: datetime
    reason: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    source_id: UUID
