from __future__ import annotations

import hashlib
from contextlib import suppress
from io import BytesIO
from pathlib import PurePath
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.config import get_settings
from ide_api.domains.auth.models import User
from ide_api.domains.documents.models import DocumentVersion
from ide_api.domains.latex.bundle import (
    LatexBundle,
    LatexBundleError,
    build_single_file_bundle,
    read_latex_bundle,
    replace_entrypoint_source,
)
from ide_api.domains.latex.compilation import LatexCompilationError, TectonicCompiler
from ide_api.domains.latex.conversion import DocxConversionError, PandocDocxConverter
from ide_api.domains.latex.models import LatexConversionReview, LatexRevision
from ide_api.domains.latex.repository import LatexRepository
from ide_api.domains.latex.schemas import (
    ConversionReviewCreate,
    LatexProjectResponse,
    LatexSourceRevisionCreate,
)
from ide_api.infrastructure.object_storage import ObjectStorage


class LatexServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class LatexProjectNotFoundError(LatexServiceError):
    pass


class LatexTransitionError(LatexServiceError):
    pass


class LatexProcessingError(LatexServiceError):
    pass


class LatexStorageError(LatexServiceError):
    pass


class LatexPersistenceError(LatexServiceError):
    pass


class LatexProjectService:
    def __init__(
        self,
        session: AsyncSession,
        storage: ObjectStorage,
        converter: PandocDocxConverter | None = None,
        compiler: TectonicCompiler | None = None,
    ) -> None:
        self._session = session
        self._storage = storage
        self._repository = LatexRepository(session)
        self._converter = converter or PandocDocxConverter()
        self._compiler = compiler or TectonicCompiler(
            only_cached=get_settings().tectonic_only_cached
        )

    async def ensure_initial_revision(self, document_id: UUID, actor: User) -> LatexRevision:
        version = await self._latest_original(document_id, lock=True)
        existing = await self._repository.latest_revision(document_id, for_update=True)
        if existing is not None:
            return existing
        original = self._download(version.object_key)
        if hashlib.sha256(original).hexdigest() != version.sha256:
            raise LatexStorageError(
                "original_integrity_failed", "Stored original failed integrity verification."
            )

        if version.input_kind == "latex_project":
            try:
                bundle = (
                    build_single_file_bundle(original, PurePath(version.original_filename).name)
                    if PurePath(version.original_filename).suffix.lower() == ".tex"
                    else read_latex_bundle(original)
                )
            except LatexBundleError as error:
                raise LatexProcessingError(error.code, error.message) from error
            origin = "latex_upload"
            conversion_status = "not_required"
        elif version.input_kind == "docx_import":
            try:
                bundle = self._converter.convert(original)
            except DocxConversionError as error:
                error_type = (
                    LatexStorageError
                    if error.code == "converter_unavailable"
                    else LatexProcessingError
                )
                raise error_type(error.code, error.message) from error
            origin = "docx_conversion"
            conversion_status = "pending_review"
        else:
            raise LatexProcessingError(
                "unsupported_latex_input", "This document cannot be used as a LaTeX project."
            )

        return await self._store_revision(
            document_id=document_id,
            bundle=bundle,
            actor=actor,
            origin=origin,
            conversion_status=conversion_status,
        )

    async def get_project(self, document_id: UUID) -> LatexProjectResponse:
        revision = await self._latest_revision_or_error(document_id)
        bundle = self._verified_bundle(revision)
        return self._to_response(revision, bundle)

    async def create_source_revision(
        self,
        document_id: UUID,
        payload: LatexSourceRevisionCreate,
        actor: User,
    ) -> LatexProjectResponse:
        version = await self._latest_original(document_id, lock=True)
        revision = await self._latest_revision_or_error(document_id, lock=True)
        if revision.id != payload.expected_revision_id:
            raise LatexTransitionError("stale_revision", "The project has a newer revision.")
        bundle = self._verified_bundle(revision)
        try:
            updated_bundle = replace_entrypoint_source(bundle, payload.source)
        except LatexBundleError as error:
            raise LatexProcessingError(error.code, error.message) from error
        created = await self._store_revision(
            document_id=document_id,
            bundle=updated_bundle,
            actor=actor,
            origin="web_edit",
            conversion_status=(
                "pending_review" if version.input_kind == "docx_import" else "not_required"
            ),
        )
        return self._to_response(created, updated_bundle)

    async def review_conversion(
        self,
        document_id: UUID,
        payload: ConversionReviewCreate,
        actor: User,
    ) -> LatexProjectResponse:
        await self._latest_original(document_id, lock=True)
        revision = await self._latest_revision_or_error(document_id, lock=True)
        if revision.id != payload.expected_revision_id:
            raise LatexTransitionError("stale_revision", "The project has a newer revision.")
        if revision.conversion_status != "pending_review" or revision.compile_status != "succeeded":
            raise LatexTransitionError(
                "invalid_conversion_transition", "This revision cannot be reviewed."
            )
        reason = payload.reason.strip()
        if not reason:
            raise LatexProcessingError("invalid_review_reason", "A review reason is required.")
        bundle = self._verified_bundle(revision)
        self._repository.add_review(
            LatexConversionReview(
                revision_id=revision.id,
                decision=payload.decision.value,
                reason=reason,
                decided_by_id=actor.id,
                decider=actor,
            )
        )
        revision.conversion_status = payload.decision.value
        await self._commit([])
        return self._to_response(revision, bundle)

    async def get_preview(self, document_id: UUID) -> tuple[bytes, str]:
        revision = await self._latest_revision_or_error(document_id)
        self._verified_bundle(revision)
        if (
            revision.compile_status != "succeeded"
            or revision.compiled_pdf_object_key is None
            or revision.compiled_pdf_sha256 is None
        ):
            raise LatexProcessingError(
                "preview_unavailable", "A compiled preview is not available."
            )
        pdf = self._download(revision.compiled_pdf_object_key)
        if hashlib.sha256(pdf).hexdigest() != revision.compiled_pdf_sha256:
            raise LatexStorageError(
                "preview_integrity_failed",
                "Stored compiled preview failed integrity verification.",
            )
        return pdf, f"{document_id}.pdf"

    async def get_bundle(self, document_id: UUID) -> tuple[bytes, str]:
        revision = await self._latest_revision_or_error(document_id)
        bundle = self._verified_bundle(revision)
        return bundle.data, f"{document_id}.zip"

    async def _latest_original(self, document_id: UUID, *, lock: bool) -> DocumentVersion:
        statement = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.created_at.desc(), DocumentVersion.id.desc())
            .limit(1)
        )
        if lock:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        version = result.scalar_one_or_none()
        if version is None:
            raise LatexProjectNotFoundError("document_not_found", "Document not found.")
        return version

    async def _latest_revision_or_error(
        self, document_id: UUID, *, lock: bool = False
    ) -> LatexRevision:
        revision = await self._repository.latest_revision(document_id, for_update=lock)
        if revision is None:
            raise LatexProjectNotFoundError("latex_project_not_found", "LaTeX project not found.")
        return revision

    async def _store_revision(
        self,
        *,
        document_id: UUID,
        bundle: LatexBundle,
        actor: User,
        origin: str,
        conversion_status: str,
    ) -> LatexRevision:
        uploaded_keys: list[str] = []
        try:
            source_key = self._upload(bundle.data)
            uploaded_keys.append(source_key)
            compile_status = "succeeded"
            compile_log: str | None = None
            pdf_key: str | None = None
            pdf_sha256: str | None = None
            try:
                result = self._compiler.compile(bundle)
                compile_log = result.log[: 64 * 1024] or None
                pdf_sha256 = hashlib.sha256(result.pdf).hexdigest()
                pdf_key = self._upload(result.pdf)
                uploaded_keys.append(pdf_key)
            except LatexCompilationError as error:
                compile_status = "failed"
                compile_log = (error.log or error.message)[: 64 * 1024]
            revision = LatexRevision(
                document_id=document_id,
                source_object_key=source_key,
                source_sha256=bundle.sha256,
                entrypoint=bundle.entrypoint,
                origin=origin,
                conversion_status=conversion_status,
                compile_status=compile_status,
                compiled_pdf_object_key=pdf_key,
                compiled_pdf_sha256=pdf_sha256,
                compile_log=compile_log,
                created_by_id=actor.id,
                creator=actor,
            )
            self._repository.add_revision(revision)
            await self._commit(uploaded_keys)
            return revision
        except LatexStorageError:
            self._delete_uploaded(uploaded_keys)
            raise
        except LatexPersistenceError:
            raise
        except Exception as error:
            self._delete_uploaded(uploaded_keys)
            raise LatexStorageError(
                "latex_storage_failed", "LaTeX project storage is unavailable."
            ) from error

    def _verified_bundle(self, revision: LatexRevision) -> LatexBundle:
        data = self._download(revision.source_object_key)
        if hashlib.sha256(data).hexdigest() != revision.source_sha256:
            raise LatexStorageError(
                "bundle_integrity_failed", "Stored LaTeX bundle failed integrity verification."
            )
        try:
            return read_latex_bundle(data)
        except LatexBundleError as error:
            raise LatexProcessingError(error.code, error.message) from error

    def _download(self, object_key: str) -> bytes:
        try:
            stream = self._storage.download(object_key)
            try:
                return stream.read()
            finally:
                close = getattr(stream, "close", None)
                if close is not None:
                    close()
        except LatexServiceError:
            raise
        except Exception as error:
            raise LatexStorageError(
                "latex_storage_failed", "LaTeX project storage is unavailable."
            ) from error

    def _upload(self, data: bytes) -> str:
        try:
            return self._storage.upload(BytesIO(data))
        except Exception as error:
            raise LatexStorageError(
                "latex_storage_failed", "LaTeX project storage is unavailable."
            ) from error

    async def _commit(self, uploaded_keys: list[str]) -> None:
        try:
            await self._session.commit()
        except Exception as error:
            await self._session.rollback()
            self._delete_uploaded(uploaded_keys)
            raise LatexPersistenceError(
                "latex_persistence_failed", "LaTeX project persistence is unavailable."
            ) from error

    def _delete_uploaded(self, object_keys: list[str]) -> None:
        for object_key in object_keys:
            with suppress(Exception):
                self._storage.delete(object_key)

    @staticmethod
    def _to_response(revision: LatexRevision, bundle: LatexBundle) -> LatexProjectResponse:
        return LatexProjectResponse(
            revision_id=revision.id,
            document_id=revision.document_id,
            entrypoint=revision.entrypoint,
            source=bundle.source,
            source_sha256=revision.source_sha256,
            files=list(bundle.files),
            origin=revision.origin,
            conversion_status=revision.conversion_status,
            compile_status=revision.compile_status,
            compile_log=revision.compile_log,
            compiled_pdf_sha256=revision.compiled_pdf_sha256,
            preview_available=(
                revision.compile_status == "succeeded"
                and revision.compiled_pdf_object_key is not None
            ),
            created_at=revision.created_at,
        )
