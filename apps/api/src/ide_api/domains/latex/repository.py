from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.domains.latex.models import LatexConversionReview, LatexRevision


class LatexRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add_revision(self, revision: LatexRevision) -> None:
        self._session.add(revision)

    async def latest_revision(
        self, document_id: UUID, *, for_update: bool = False
    ) -> LatexRevision | None:
        statement = (
            select(LatexRevision)
            .where(LatexRevision.document_id == document_id)
            .order_by(LatexRevision.created_at.desc(), LatexRevision.id.desc())
            .limit(1)
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    def add_review(self, review: LatexConversionReview) -> None:
        self._session.add(review)

    async def reviews_for_document(self, document_id: UUID) -> list[LatexConversionReview]:
        result = await self._session.execute(
            select(LatexConversionReview)
            .join(LatexConversionReview.revision)
            .where(LatexRevision.document_id == document_id)
            .order_by(LatexConversionReview.decided_at, LatexConversionReview.id)
        )
        return list(result.scalars())
