from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ide_api.domains.documents.models import DocumentVersion
from ide_api.domains.formatting.models import ExternalEditResult, FormatCheck, FormatDifference


class FormattingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, entity: ExternalEditResult | FormatCheck | FormatDifference) -> None:
        self._session.add(entity)

    async def get_document_version(self, document_version_id: UUID) -> DocumentVersion | None:
        result = await self._session.execute(
            select(DocumentVersion).where(DocumentVersion.id == document_version_id)
        )
        return result.scalar_one_or_none()

    async def get_external_edit_result(
        self, external_edit_result_id: UUID
    ) -> ExternalEditResult | None:
        result = await self._session.execute(
            select(ExternalEditResult)
            .options(
                selectinload(ExternalEditResult.document_version),
                selectinload(ExternalEditResult.format_check).selectinload(FormatCheck.differences),
            )
            .where(ExternalEditResult.id == external_edit_result_id)
        )
        return result.scalar_one_or_none()

    async def get_format_check(self, external_edit_result_id: UUID) -> FormatCheck | None:
        result = await self._session.execute(
            select(FormatCheck)
            .options(selectinload(FormatCheck.differences))
            .where(FormatCheck.external_edit_result_id == external_edit_result_id)
        )
        return result.scalar_one_or_none()

    async def get_difference(self, difference_id: UUID) -> FormatDifference | None:
        result = await self._session.execute(
            select(FormatDifference)
            .options(
                selectinload(FormatDifference.format_check).selectinload(
                    FormatCheck.external_edit_result
                )
            )
            .where(FormatDifference.id == difference_id)
        )
        return result.scalar_one_or_none()

    async def list_by_document_id(self, document_id: UUID) -> list[ExternalEditResult]:
        result = await self._session.execute(
            select(ExternalEditResult)
            .options(selectinload(ExternalEditResult.format_check))
            .where(ExternalEditResult.document_id == document_id)
            .order_by(ExternalEditResult.created_at.desc())
        )
        return list(result.scalars())
