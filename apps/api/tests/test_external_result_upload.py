from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import Response, UploadFile

from ide_api.config import Settings
from ide_api.domains.documents.models import DocumentVersion
from ide_api.domains.formatting import router as formatting_router
from ide_api.domains.formatting.service import (
    ExternalEditResultUploadError,
    FormatMismatchError,
    FormattingService,
    UnsupportedExternalEditResultError,
)

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MEDIA_TYPE = "application/pdf"


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def upload(self, content: object) -> str:
        object_key = f"external/{uuid4()}"
        self.objects[object_key] = content.read()
        return object_key

    def delete(self, object_key: str) -> None:
        self.deleted.append(object_key)
        self.objects.pop(object_key, None)


class FakeSession:
    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


def _source(input_kind: str = "editable_docx") -> DocumentVersion:
    return DocumentVersion(
        id=uuid4(),
        document_id=uuid4(),
        original_filename="source.docx",
        media_type=DOCX_MEDIA_TYPE,
        size_bytes=1,
        sha256="0" * 64,
        object_key="source-object",
        created_by_id=uuid4(),
        input_kind=input_kind,
    )


def _upload(filename: str, content_type: str, content: bytes) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers={"content-type": content_type},
    )


def _service(source: DocumentVersion, storage: FakeStorage) -> FormattingService:
    service = FormattingService(
        FakeSession(),
        SimpleNamespace(),
        storage=storage,
        settings=Settings(max_upload_size_bytes=2 * 1024 * 1024),
    )

    async def get_document_version(document_version_id: object) -> DocumentVersion | None:
        return source if document_version_id == source.id else None

    def add(result: object) -> None:
        now = datetime.now(UTC)
        result.id = uuid4()
        result.created_at = now
        result.format_check.id = uuid4()
        result.format_check.external_edit_result_id = result.id
        result.format_check.created_at = now
        result.format_check.updated_at = now

    service._repository.get_document_version = get_document_version  # type: ignore[method-assign]
    service._repository.add = add  # type: ignore[method-assign]
    return service


@pytest.mark.asyncio
async def test_collects_same_format_docx_and_hides_internal_object_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source()
    storage = FakeStorage()
    service = _service(source, storage)
    monkeypatch.setattr(formatting_router, "_service", lambda *_: service)
    monkeypatch.setattr(formatting_router, "ObjectStorage", lambda: storage)

    response = Response()
    body = await formatting_router.collect_external_edit_result(
        response=response,
        db_session=FakeSession(),
        current_user=SimpleNamespace(id=uuid4()),
        document_id=source.document_id,
        document_version_id=source.id,
        file=_upload("edited.docx", DOCX_MEDIA_TYPE, b"edited DOCX bytes"),
    )

    route = next(
        item
        for item in formatting_router.router.routes
        if item.path == "/formatting/external-results" and "POST" in item.methods
    )
    assert route.status_code == 202
    assert response.headers["location"] == f"/api/v1/formatting/external-results/{body['id']}"
    assert "object_key" not in body
    assert len(storage.objects) == 1
    assert next(iter(storage.objects.values())) == b"edited DOCX bytes"
    assert source.object_key == "source-object"


@pytest.mark.asyncio
async def test_blocks_docx_to_pdf_before_storing() -> None:
    source = _source()
    storage = FakeStorage()

    with pytest.raises(FormatMismatchError):
        await _service(source, storage).collect_uploaded_external_edit_result(
            created_by_id=uuid4(),
            document_id=source.document_id,
            document_version_id=source.id,
            upload=_upload("edited.pdf", PDF_MEDIA_TYPE, b"%PDF"),
        )

    assert storage.objects == {}


@pytest.mark.asyncio
async def test_blocks_scanned_pdf_before_storing() -> None:
    source = _source(input_kind="scanned_pdf")
    source.media_type = PDF_MEDIA_TYPE
    storage = FakeStorage()

    with pytest.raises(UnsupportedExternalEditResultError):
        await _service(source, storage).collect_uploaded_external_edit_result(
            created_by_id=uuid4(),
            document_id=source.document_id,
            document_version_id=source.id,
            upload=_upload("edited.pdf", PDF_MEDIA_TYPE, b"%PDF"),
        )

    assert storage.objects == {}


@pytest.mark.asyncio
async def test_blocks_empty_file_before_storing() -> None:
    source = _source()
    storage = FakeStorage()

    with pytest.raises(ExternalEditResultUploadError, match="must not be empty"):
        await _service(source, storage).collect_uploaded_external_edit_result(
            created_by_id=uuid4(),
            document_id=source.document_id,
            document_version_id=source.id,
            upload=_upload("edited.docx", DOCX_MEDIA_TYPE, b""),
        )

    assert storage.objects == {}
