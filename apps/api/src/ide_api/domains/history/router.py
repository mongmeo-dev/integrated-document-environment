from uuid import UUID

from fastapi import APIRouter, Query

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.domains.auth.schemas import ApiError
from ide_api.domains.history.schemas import HistoryEvent
from ide_api.domains.history.service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get(
    "",
    operation_id="listHistoryEvents",
    response_model=list[HistoryEvent],
    responses={401: {"model": ApiError}},
)
async def list_history_events(
    db_session: DbSession,
    _: CurrentUser,
    document_id: UUID | None = None,
    filter: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[HistoryEvent]:
    return await HistoryService(db_session).list_events(
        document_id=document_id,
        event_filter=filter,
        limit=limit,
        offset=offset,
    )
