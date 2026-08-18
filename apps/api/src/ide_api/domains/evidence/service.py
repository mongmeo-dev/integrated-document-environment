from contextlib import suppress
from datetime import UTC, datetime
from hashlib import sha256
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.config import get_settings
from ide_api.domains.evidence.models import DocumentEvidenceLink, EvidenceItem
from ide_api.domains.evidence.repository import EvidenceRepository
from ide_api.domains.evidence.schemas import (
    DocumentEvidenceLinkCreate,
    EvidenceFreshness,
    EvidenceItemCreate,
    EvidenceItemUpdate,
    EvidenceLinkStatus,
)
from ide_api.infrastructure.object_storage import ObjectStorage

UPLOAD_CHUNK_SIZE = 1024 * 1024


class UploadedFile(Protocol):
    filename: str | None
    content_type: str | None

    async def read(self, size: int = -1) -> bytes: ...


class EvidenceFileEmptyError(Exception):
    pass


class EvidenceFileTooLargeError(Exception):
    pass


class EvidenceFileNotAvailableError(Exception):
    pass


class EvidenceItemNotFoundError(Exception):
    pass


class DocumentEvidenceLinkNotFoundError(Exception):
    pass


class InvalidEvidenceLinkTransitionError(Exception):
    pass


class InvalidFreshnessReviewError(Exception):
    pass


class EvidenceService:
    def __init__(self, session: AsyncSession, storage: ObjectStorage | None = None) -> None:
        self._session = session
        self._repository = EvidenceRepository(session)
        self._storage = storage or ObjectStorage()

    async def create_evidence_item(self, *, data: EvidenceItemCreate) -> EvidenceItem:
        evidence = EvidenceItem(
            evidence_type=data.evidence_type.value,
            title=data.title,
            description=data.description,
            reference=data.reference,
            location=data.location,
            version=data.version,
        )
        self._repository.add(evidence)
        await self._session.commit()
        return evidence

    async def create_uploaded_evidence_item(
        self,
        *,
        title: str,
        description: str,
        version: str | None,
        file: UploadedFile,
    ) -> EvidenceItem:
        filename = file.filename
        if not filename:
            raise EvidenceFileEmptyError

        maximum_size = get_settings().max_upload_size_bytes
        digest = sha256()
        size_bytes = 0
        with SpooledTemporaryFile(mode="w+b") as content:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                size_bytes += len(chunk)
                if size_bytes > maximum_size:
                    raise EvidenceFileTooLargeError
                digest.update(chunk)
                content.write(chunk)

            if size_bytes == 0:
                raise EvidenceFileEmptyError

            content.seek(0)
            object_key = self._storage.upload(content)

        evidence = EvidenceItem(
            evidence_type="upload",
            title=title,
            description=description,
            version=version,
            object_key=object_key,
            original_filename=filename,
            media_type=file.content_type or "application/octet-stream",
            size_bytes=size_bytes,
            sha256=digest.hexdigest(),
        )
        self._repository.add(evidence)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            with suppress(Exception):
                self._storage.delete(object_key)
            raise
        return evidence

    async def download_evidence_file(self, *, evidence_id: UUID) -> tuple[EvidenceItem, BinaryIO]:
        evidence = await self._get_evidence_item(evidence_id)
        if evidence.evidence_type != "upload" or evidence.object_key is None:
            raise EvidenceFileNotAvailableError
        return evidence, self._storage.download(evidence.object_key)

    async def list_evidence_items(self) -> list[EvidenceItem]:
        return await self._repository.list_evidence_items()

    async def get_evidence_item(self, *, evidence_id: UUID) -> EvidenceItem:
        return await self._get_evidence_item(evidence_id)

    async def update_evidence_item(
        self, *, evidence_id: UUID, data: EvidenceItemUpdate
    ) -> EvidenceItem:
        evidence = await self._get_evidence_item(evidence_id)
        changed = False
        for field in data.model_fields_set:
            value = getattr(data, field)
            if getattr(evidence, field) != value:
                setattr(evidence, field, value)
                changed = True
        if changed:
            await self._mark_links_stale(
                await self._repository.list_links_by_evidence_id(evidence_id)
            )
        await self._session.commit()
        return evidence

    async def create_document_evidence_link(
        self, *, data: DocumentEvidenceLinkCreate
    ) -> DocumentEvidenceLink:
        link = DocumentEvidenceLink(
            document_id=data.document_id,
            evidence_id=data.evidence_id,
            reason=data.reason,
            status=EvidenceLinkStatus.CANDIDATE.value,
            freshness=EvidenceFreshness.CURRENT.value,
        )
        self._repository.add(link)
        await self._session.commit()
        return link

    async def list_document_evidence_links(
        self, *, document_id: UUID
    ) -> list[DocumentEvidenceLink]:
        return await self._repository.list_links_by_document_id(document_id)

    async def get_document_evidence_link(self, *, link_id: UUID) -> DocumentEvidenceLink:
        return await self._get_link(link_id)

    async def confirm_document_evidence_link(
        self, *, link_id: UUID, decided_by_id: UUID
    ) -> DocumentEvidenceLink:
        return await self._decide_link(link_id, EvidenceLinkStatus.CONFIRMED, decided_by_id)

    async def reject_document_evidence_link(
        self, *, link_id: UUID, decided_by_id: UUID
    ) -> DocumentEvidenceLink:
        return await self._decide_link(link_id, EvidenceLinkStatus.REJECTED, decided_by_id)

    async def review_document_evidence_freshness(
        self, *, link_id: UUID, reviewed_by_id: UUID
    ) -> DocumentEvidenceLink:
        link = await self._get_link(link_id)
        if EvidenceLinkStatus(link.status) is not EvidenceLinkStatus.CONFIRMED:
            raise InvalidFreshnessReviewError
        if EvidenceFreshness(link.freshness) is not EvidenceFreshness.STALE:
            raise InvalidFreshnessReviewError

        link.freshness = EvidenceFreshness.CURRENT.value
        link.reviewed_by_id = reviewed_by_id
        link.reviewed_at = datetime.now(UTC)
        await self._session.commit()
        return link

    async def mark_links_stale_for_document_change(self, *, document_id: UUID) -> None:
        await self._mark_links_stale(await self._repository.list_links_by_document_id(document_id))
        await self._session.commit()

    async def mark_links_stale_for_evidence_change(self, *, evidence_id: UUID) -> None:
        await self._get_evidence_item(evidence_id)
        await self._mark_links_stale(await self._repository.list_links_by_evidence_id(evidence_id))
        await self._session.commit()

    async def _decide_link(
        self, link_id: UUID, status: EvidenceLinkStatus, decided_by_id: UUID
    ) -> DocumentEvidenceLink:
        link = await self._get_link(link_id)
        if EvidenceLinkStatus(link.status) is not EvidenceLinkStatus.CANDIDATE:
            raise InvalidEvidenceLinkTransitionError

        link.status = status.value
        link.decided_by_id = decided_by_id
        link.decided_at = datetime.now(UTC)
        await self._session.commit()
        return link

    async def _mark_links_stale(self, links: list[DocumentEvidenceLink]) -> None:
        for link in links:
            link.freshness = EvidenceFreshness.STALE.value

    async def _get_evidence_item(self, evidence_id: UUID) -> EvidenceItem:
        evidence = await self._repository.get_evidence_item_by_id(evidence_id)
        if evidence is None:
            raise EvidenceItemNotFoundError
        return evidence

    async def _get_link(self, link_id: UUID) -> DocumentEvidenceLink:
        link = await self._repository.get_link_by_id(link_id)
        if link is None:
            raise DocumentEvidenceLinkNotFoundError
        return link
