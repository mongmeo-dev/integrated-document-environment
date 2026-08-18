from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ide_api.domains.changes.models import ChangeProposal, ChangeRequest


class ChangeRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, change_request: ChangeRequest | ChangeProposal) -> None:
        self._session.add(change_request)

    async def list_by_document_id(self, document_id: UUID) -> list[ChangeRequest]:
        result = await self._session.execute(
            select(ChangeRequest)
            .where(ChangeRequest.document_id == document_id)
            .order_by(ChangeRequest.created_at.desc())
        )
        return list(result.scalars())

    async def get_by_id_with_proposals(self, change_request_id: UUID) -> ChangeRequest | None:
        result = await self._session.execute(
            select(ChangeRequest)
            .options(selectinload(ChangeRequest.proposals))
            .where(ChangeRequest.id == change_request_id)
        )
        return result.scalar_one_or_none()
