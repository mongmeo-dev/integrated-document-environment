from pathlib import Path

import pytest
from fastapi import UploadFile

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User
from ide_api.domains.documents.service import DocumentService

SAMPLE_DOCS = Path(__file__).parents[3] / "fixture" / "sample-docs"
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class RecordingStorage:
    def __init__(self) -> None:
        self.sizes: list[int] = []

    def upload(self, content: object) -> str:
        stream = content
        size = 0
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
        self.sizes.append(size)
        return f"test/original-{len(self.sizes)}"

    def delete(self, object_key: str) -> None:
        raise AssertionError(f"Unexpected compensation delete: {object_key}")


@pytest.mark.asyncio
async def test_registers_all_sample_docx_files_without_loading_them_as_fixtures() -> None:
    paths = sorted(SAMPLE_DOCS.glob("*.docx"))
    assert len(paths) == 7

    storage = RecordingStorage()
    async with async_session() as session:
        creator = User(
            email=f"sample-docs-{id(storage)}@example.com",
            display_name="Sample Docs",
            password_hash=hash_password("sample-password"),
        )
        session.add(creator)
        await session.commit()
        service = DocumentService(session, storage=storage)

        for path in paths:
            with path.open("rb") as source:
                upload = UploadFile(
                    file=source,
                    filename=path.name,
                    headers={"content-type": DOCX_MEDIA_TYPE},
                )
                document = await service.register_original(upload, creator)
                response = service.to_response(document)

            assert response.original_file.original_filename == path.name
            assert response.original_file.size_bytes == path.stat().st_size
            assert len(response.original_file.sha256) == 64
            assert response.status == "queued"
            assert response.capabilities.analysis is False

    assert storage.sizes == [path.stat().st_size for path in paths]
    assert max(storage.sizes) > 200_000_000
