import hashlib
from collections.abc import Sequence
from pathlib import PurePath
from tempfile import SpooledTemporaryFile
from typing import Protocol
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.config import Settings, get_settings
from ide_api.domains.documents.models import DocumentVersion
from ide_api.domains.formatting.models import ExternalEditResult, FormatCheck, FormatDifference
from ide_api.domains.formatting.repository import FormattingRepository
from ide_api.domains.formatting.schemas import (
    DetectedFormatDifference,
    ExternalEditResultCreate,
    ExternalEditResultResponse,
    ExternalEditResultStatus,
    FormatCheckResponse,
    OriginalFormat,
    VisualReviewStatus,
)
from ide_api.infrastructure.object_storage import ObjectStorage

_DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_PDF_MEDIA_TYPE = "application/pdf"
_CHUNK_SIZE = 1024 * 1024


class DocumentVersionNotFoundError(Exception):
    pass


class ExternalEditResultNotFoundError(Exception):
    pass


class UnsupportedExternalEditResultError(Exception):
    pass


class FormatMismatchError(Exception):
    pass


class InvalidFormatCheckTransitionError(Exception):
    pass


class FormatApprovalBlockedError(Exception):
    pass


class ExternalEditResultUploadError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class ExternalEditResultStorageError(Exception):
    pass


class ExternalEditResultPersistenceError(Exception):
    pass


class FormatComparisonRunner(Protocol):
    async def compare(
        self,
        *,
        original: DocumentVersion,
        result: ExternalEditResult,
    ) -> Sequence[DetectedFormatDifference]: ...


class FormattingService:
    def __init__(
        self,
        session: AsyncSession,
        comparison_runner: FormatComparisonRunner,
        storage: ObjectStorage | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._repository = FormattingRepository(session)
        self._comparison_runner = comparison_runner
        self._storage = storage
        self._settings = settings or get_settings()

    async def collect_uploaded_external_edit_result(
        self,
        *,
        created_by_id: UUID,
        document_id: UUID,
        document_version_id: UUID,
        upload: UploadFile,
    ) -> ExternalEditResult:
        document_version = await self._repository.get_document_version(document_version_id)
        if document_version is None:
            raise DocumentVersionNotFoundError
        if document_version.document_id != document_id:
            raise FormatMismatchError

        original_format = self._expected_format(document_version)
        filename = upload.filename or ""
        media_type = self._media_type(original_format)
        if PurePath(filename).suffix.lower() != f".{original_format.value}" or (
            upload.content_type != media_type
        ):
            raise FormatMismatchError

        size_bytes = 0
        digest = hashlib.sha256()
        with SpooledTemporaryFile(max_size=_CHUNK_SIZE, mode="w+b") as content:
            while chunk := await upload.read(_CHUNK_SIZE):
                size_bytes += len(chunk)
                if size_bytes > self._settings.max_upload_size_bytes:
                    raise ExternalEditResultUploadError(
                        "file_too_large", "File exceeds the maximum upload size."
                    )
                digest.update(chunk)
                content.write(chunk)

            if size_bytes == 0:
                raise ExternalEditResultUploadError("empty_file", "File must not be empty.")

            content.seek(0)
            try:
                if self._storage is None:
                    raise RuntimeError("Object storage is not configured.")
                object_key = self._storage.upload(content)
            except Exception as error:
                raise ExternalEditResultStorageError from error

        try:
            return await self.collect_external_edit_result(
                created_by_id=created_by_id,
                data=ExternalEditResultCreate(
                    document_id=document_id,
                    document_version_id=document_version_id,
                    original_format=original_format,
                    original_filename=filename,
                    media_type=media_type,
                    size_bytes=size_bytes,
                    sha256=digest.hexdigest(),
                    object_key=object_key,
                ),
            )
        except Exception:
            try:
                if self._storage is not None:
                    self._storage.delete(object_key)
            except Exception:
                pass
            raise

    async def collect_external_edit_result(
        self,
        *,
        created_by_id: UUID,
        data: ExternalEditResultCreate,
    ) -> ExternalEditResult:
        document_version = await self._repository.get_document_version(data.document_version_id)
        if document_version is None:
            raise DocumentVersionNotFoundError
        if document_version.document_id != data.document_id:
            raise FormatMismatchError

        expected_format = self._expected_format(document_version)
        if data.original_format is not expected_format or data.media_type != self._media_type(
            expected_format
        ):
            raise FormatMismatchError

        result = ExternalEditResult(
            document_id=data.document_id,
            document_version_id=data.document_version_id,
            original_format=expected_format.value,
            original_filename=data.original_filename,
            media_type=data.media_type,
            size_bytes=data.size_bytes,
            sha256=data.sha256,
            object_key=data.object_key,
            status=ExternalEditResultStatus.UPLOADED.value,
            created_by_id=created_by_id,
        )
        result.format_check = FormatCheck(
            automatic_check_completed=False,
            visual_review=VisualReviewStatus.PENDING.value,
            unresolved_difference_count=0,
        )
        result.format_check.differences = []
        self._repository.add(result)
        try:
            await self._session.commit()
        except Exception as error:
            await self._session.rollback()
            raise ExternalEditResultPersistenceError from error
        return result

    async def run_automatic_check(self, *, external_edit_result_id: UUID) -> FormatCheck:
        result = await self._get_external_edit_result(external_edit_result_id)
        check = self._require_check(result)
        if ExternalEditResultStatus(result.status) is not ExternalEditResultStatus.UPLOADED:
            raise InvalidFormatCheckTransitionError

        result.status = ExternalEditResultStatus.CHECKING.value
        await self._session.commit()

        differences = await self._comparison_runner.compare(
            original=result.document_version,
            result=result,
        )
        await self._complete_automatic_check(check, differences)
        return check

    async def complete_visual_review(
        self,
        *,
        external_edit_result_id: UUID,
        visual_review: VisualReviewStatus,
    ) -> FormatCheck:
        if visual_review is VisualReviewStatus.PENDING:
            raise InvalidFormatCheckTransitionError

        result = await self._get_external_edit_result(external_edit_result_id)
        check = self._require_check(result)
        if (
            not check.automatic_check_completed
            or VisualReviewStatus(check.visual_review) is not VisualReviewStatus.PENDING
            or ExternalEditResultStatus(result.status) is not ExternalEditResultStatus.CHECKING
        ):
            raise InvalidFormatCheckTransitionError

        check.visual_review = visual_review.value
        if visual_review is VisualReviewStatus.PASSED and check.unresolved_difference_count == 0:
            result.status = ExternalEditResultStatus.PASSED.value
        else:
            # A visual failure or any detected difference requires a new external result.
            result.status = ExternalEditResultStatus.NEEDS_REVISION.value
        await self._session.commit()
        return check

    async def resolve_difference(self, *, difference_id: UUID) -> FormatDifference:
        difference = await self._repository.get_difference(difference_id)
        if difference is None:
            raise ExternalEditResultNotFoundError
        if difference.resolved:
            raise InvalidFormatCheckTransitionError

        check = difference.format_check
        result = check.external_edit_result
        if ExternalEditResultStatus(result.status) is not ExternalEditResultStatus.NEEDS_REVISION:
            raise InvalidFormatCheckTransitionError

        difference.resolved = True
        check.unresolved_difference_count -= 1
        await self._session.commit()
        return difference

    async def get_external_edit_result(
        self, *, external_edit_result_id: UUID
    ) -> ExternalEditResultResponse:
        result = await self._get_external_edit_result(external_edit_result_id)
        return ExternalEditResultResponse.model_validate(result)

    async def get_format_check(self, *, external_edit_result_id: UUID) -> FormatCheckResponse:
        check = await self._repository.get_format_check(external_edit_result_id)
        if check is None:
            raise ExternalEditResultNotFoundError
        return FormatCheckResponse.model_validate(check)

    async def list_external_edit_results(self, *, document_id: UUID) -> list[ExternalEditResult]:
        return await self._repository.list_by_document_id(document_id)

    async def is_approval_allowed(self, *, external_edit_result_id: UUID) -> bool:
        result = await self._get_external_edit_result(external_edit_result_id)
        check = self._require_check(result)
        return (
            ExternalEditResultStatus(result.status) is ExternalEditResultStatus.PASSED
            and check.automatic_check_completed
            and VisualReviewStatus(check.visual_review) is VisualReviewStatus.PASSED
            and check.unresolved_difference_count == 0
        )

    async def require_approval_allowed(self, *, external_edit_result_id: UUID) -> None:
        if not await self.is_approval_allowed(external_edit_result_id=external_edit_result_id):
            raise FormatApprovalBlockedError

    async def _complete_automatic_check(
        self,
        check: FormatCheck,
        differences: Sequence[DetectedFormatDifference],
    ) -> None:
        if check.automatic_check_completed:
            raise InvalidFormatCheckTransitionError

        for item in differences:
            check.differences.append(
                FormatDifference(
                    category=item.category.value,
                    location=item.location,
                    original_value=item.original_value,
                    proposed_value=item.proposed_value,
                )
            )
        check.automatic_check_completed = True
        check.unresolved_difference_count = len(differences)
        await self._session.commit()

    async def _get_external_edit_result(self, external_edit_result_id: UUID) -> ExternalEditResult:
        result = await self._repository.get_external_edit_result(external_edit_result_id)
        if result is None:
            raise ExternalEditResultNotFoundError
        return result

    @staticmethod
    def _require_check(result: ExternalEditResult) -> FormatCheck:
        if result.format_check is None:
            raise InvalidFormatCheckTransitionError
        return result.format_check

    @staticmethod
    def _expected_format(document_version: DocumentVersion) -> OriginalFormat:
        if document_version.input_kind == "editable_docx":
            return OriginalFormat.DOCX
        if document_version.input_kind == "text_pdf":
            return OriginalFormat.PDF
        raise UnsupportedExternalEditResultError

    @staticmethod
    def _media_type(original_format: OriginalFormat) -> str:
        if original_format is OriginalFormat.DOCX:
            return _DOCX_MEDIA_TYPE
        return _PDF_MEDIA_TYPE
