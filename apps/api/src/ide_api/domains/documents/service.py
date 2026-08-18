from __future__ import annotations

import hashlib
from pathlib import PurePath
from tempfile import SpooledTemporaryFile
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.config import Settings, get_settings
from ide_api.domains.auth.models import User
from ide_api.domains.documents.models import Document, DocumentVersion
from ide_api.domains.documents.repository import DocumentRepository
from ide_api.domains.documents.schemas import (
    DocumentCapabilities,
    DocumentCreator,
    DocumentResponse,
    DocumentStatus,
    OriginalFileResponse,
)
from ide_api.domains.documents.validation import DocumentValidationResult, validate_document
from ide_api.infrastructure.object_storage import ObjectStorage

_CHUNK_SIZE = 1024 * 1024
_ALLOWED_FILE_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
}


class DocumentUploadError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class DocumentNotFoundError(Exception):
    pass


class DocumentPersistenceError(Exception):
    pass


class DocumentStorageError(Exception):
    pass


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        storage: ObjectStorage | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._repository = DocumentRepository(session)
        self._storage = storage
        self._settings = settings or get_settings()

    async def register_original(
        self,
        upload: UploadFile,
        creator: User,
    ) -> Document:
        filename, media_type = self._validate_file_type(upload)
        size_bytes = 0
        digest = hashlib.sha256()

        with SpooledTemporaryFile(max_size=_CHUNK_SIZE, mode="w+b") as content:
            while chunk := await upload.read(_CHUNK_SIZE):
                size_bytes += len(chunk)
                if size_bytes > self._settings.max_upload_size_bytes:
                    raise DocumentUploadError(
                        "file_too_large",
                        "File exceeds the maximum upload size.",
                    )
                digest.update(chunk)
                content.write(chunk)

            if size_bytes == 0:
                raise DocumentUploadError("empty_file", "File must not be empty.")

            content.seek(0)
            try:
                if self._storage is None:
                    raise RuntimeError("Object storage is not configured.")
                object_key = self._storage.upload(content)
            except Exception as error:
                raise DocumentStorageError("Unable to store the uploaded file.") from error

        version = DocumentVersion(
            original_filename=filename,
            media_type=media_type,
            size_bytes=size_bytes,
            sha256=digest.hexdigest(),
            object_key=object_key,
            created_by_id=creator.id,
            creator=creator,
            status=DocumentStatus.QUEUED.value,
        )
        document = Document(versions=[version])
        self._repository.add(document)

        try:
            await self._session.commit()
        except Exception as error:
            await self._session.rollback()
            try:
                if self._storage is not None:
                    self._storage.delete(object_key)
            except Exception:
                pass
            raise DocumentPersistenceError("Unable to register the uploaded file.") from error

        return document

    async def get_document(self, document_id: UUID) -> DocumentResponse:
        document = await self._repository.get_by_id(document_id)
        if document is None or not document.versions:
            raise DocumentNotFoundError
        return self.to_response(document)

    async def validate_original(self, document_id: UUID) -> Document:
        document = await self._repository.get_by_id(document_id)
        if document is None or not document.versions:
            raise DocumentNotFoundError
        if self._storage is None:
            raise DocumentStorageError("Object storage is not configured.")

        version = document.versions[0]
        version.status = DocumentStatus.VALIDATING.value
        version.input_kind = None
        version.rejection_code = None
        version.rejection_message = None
        await self._commit_validation_state()

        try:
            result = self._validate_stored_original(version.object_key, version.media_type)
        except Exception as error:
            raise DocumentStorageError("Unable to retrieve the stored document.") from error

        if result.accepted:
            version.status = DocumentStatus.READY.value
            version.input_kind = result.input_kind
        else:
            version.status = DocumentStatus.REJECTED.value
            version.rejection_code = result.rejection_code
            version.rejection_message = result.rejection_message
        await self._commit_validation_state()
        return document

    @staticmethod
    def to_response(document: Document) -> DocumentResponse:
        version = document.versions[0]
        if version.creator is None:
            raise DocumentNotFoundError

        return DocumentResponse(
            id=document.id,
            original_file=OriginalFileResponse(
                id=version.id,
                original_filename=version.original_filename,
                media_type=version.media_type,
                size_bytes=version.size_bytes,
                sha256=version.sha256,
            ),
            status=DocumentStatus(version.status),
            input_kind=version.input_kind,
            capabilities=DocumentService._capabilities(version.input_kind),
            rejection=(
                None
                if version.rejection_code is None or version.rejection_message is None
                else {
                    "code": version.rejection_code,
                    "message": version.rejection_message,
                }
            ),
            creator=DocumentCreator(
                id=version.creator.id,
                display_name=version.creator.display_name,
            ),
            created_at=version.created_at,
        )

    @staticmethod
    def _validate_file_type(upload: UploadFile) -> tuple[str, str]:
        filename = upload.filename or ""
        extension = PurePath(filename).suffix.lower()
        expected_media_type = _ALLOWED_FILE_TYPES.get(extension)
        if expected_media_type is None or upload.content_type != expected_media_type:
            raise DocumentUploadError(
                "unsupported_file_type",
                "Only DOCX and PDF files with matching media types are supported.",
            )
        return filename, expected_media_type

    def _validate_stored_original(
        self,
        object_key: str,
        media_type: str,
    ) -> DocumentValidationResult:
        if self._storage is None:
            raise RuntimeError("Object storage is not configured.")
        stream = self._storage.download(object_key)
        try:
            with SpooledTemporaryFile(max_size=_CHUNK_SIZE, mode="w+b") as content:
                size_bytes = 0
                while chunk := stream.read(_CHUNK_SIZE):
                    size_bytes += len(chunk)
                    if size_bytes > self._settings.max_upload_size_bytes:
                        return DocumentValidationResult(
                            input_kind=None,
                            rejection_code="corrupt_document",
                            rejection_message="The stored document exceeds the maximum size.",
                        )
                    content.write(chunk)
                content.seek(0)
                return validate_document(content, media_type)
        finally:
            close = getattr(stream, "close", None)
            if close is not None:
                close()

    async def _commit_validation_state(self) -> None:
        try:
            await self._session.commit()
        except Exception as error:
            await self._session.rollback()
            raise DocumentPersistenceError("Unable to update document validation.") from error

    @staticmethod
    def _capabilities(input_kind: str | None) -> DocumentCapabilities:
        if input_kind in {"editable_docx", "text_pdf"}:
            return DocumentCapabilities(
                analysis=True,
                external_edit_round_trip=True,
                format_comparison=True,
                approved_output=True,
            )
        if input_kind == "scanned_pdf":
            return DocumentCapabilities(
                analysis=True,
                external_edit_round_trip=False,
                format_comparison=False,
                approved_output=False,
            )
        return DocumentCapabilities(
            analysis=False,
            external_edit_round_trip=False,
            format_comparison=False,
            approved_output=False,
        )
