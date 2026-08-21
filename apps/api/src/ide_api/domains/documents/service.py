from __future__ import annotations

import hashlib
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import PurePath
from tempfile import SpooledTemporaryFile
from typing import BinaryIO
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
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".pdf": {"application/pdf"},
    ".tex": {"text/x-tex", "application/x-tex", "text/plain"},
    ".zip": {"application/zip"},
}


@contextmanager
def _temporary_binary_file() -> Iterator[BinaryIO]:
    with SpooledTemporaryFile(max_size=_CHUNK_SIZE, mode="w+b") as content:
        yield content


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

    async def list_relationship_analysis_sources(
        self, *, exclude_document_id: UUID
    ) -> list[Document]:
        return await self._repository.list_ready_for_relationship_analysis(
            exclude_document_id=exclude_document_id
        )

    async def get_relationship_analysis_source(self, *, document_id: UUID) -> Document:
        document = await self._repository.get_by_id(document_id)
        if document is None or not document.versions:
            raise DocumentNotFoundError
        return document

    async def get_original(self, document_id: UUID) -> tuple[BinaryIO, str, str, ExitStack]:
        document = await self._repository.get_by_id(document_id)
        if document is None or not document.versions:
            raise DocumentNotFoundError
        if self._storage is None:
            raise DocumentStorageError("Object storage is not configured.")

        version = document.versions[0]
        resources = ExitStack()
        content = resources.enter_context(_temporary_binary_file())
        digest = hashlib.sha256()
        size_bytes = 0
        try:
            stream = self._storage.download(version.object_key)
            try:
                while chunk := stream.read(_CHUNK_SIZE):
                    size_bytes += len(chunk)
                    if size_bytes > self._settings.max_upload_size_bytes:
                        raise DocumentStorageError("Stored original exceeds the maximum size.")
                    digest.update(chunk)
                    content.write(chunk)
            finally:
                close = getattr(stream, "close", None)
                if close is not None:
                    close()
            if size_bytes != version.size_bytes or digest.hexdigest() != version.sha256:
                raise DocumentStorageError("Stored original failed integrity verification.")
            content.seek(0)
            return content, version.original_filename, version.media_type, resources
        except DocumentStorageError:
            resources.close()
            raise
        except Exception as error:
            resources.close()
            raise DocumentStorageError("Unable to retrieve the stored original.") from error

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
            result = self._validate_stored_original(
                version.object_key, version.original_filename, version.media_type
            )
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
        allowed_media_types = _ALLOWED_FILE_TYPES.get(extension, set())
        media_type = upload.content_type
        if media_type is None or media_type not in allowed_media_types:
            raise DocumentUploadError(
                "unsupported_file_type",
                "LaTeX projects are primary; DOCX is supported only as an import input. "
                "Filename and media type must match.",
            )
        return filename, media_type

    def _validate_stored_original(
        self,
        object_key: str,
        filename: str,
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
                return validate_document(content, filename, media_type)
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
        if input_kind == "latex_project":
            return DocumentCapabilities(
                analysis=True,
                source_editing=True,
                compilation=True,
                conversion_review=False,
                approved_output=True,
            )
        if input_kind == "docx_import":
            return DocumentCapabilities(
                analysis=True,
                source_editing=True,
                compilation=True,
                conversion_review=True,
                approved_output=False,
            )
        if input_kind in {"text_pdf", "scanned_pdf"}:
            return DocumentCapabilities(
                analysis=True,
                source_editing=False,
                compilation=False,
                conversion_review=False,
                approved_output=False,
            )
        return DocumentCapabilities(
            analysis=False,
            source_editing=False,
            compilation=False,
            conversion_review=False,
            approved_output=False,
        )
