import asyncio
import hashlib
from collections.abc import Generator
from io import BytesIO
from types import SimpleNamespace
from typing import ClassVar
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User, UserSession
from ide_api.domains.evidence.models import DocumentEvidenceLink, EvidenceItem


class FakeObjectStorage:
    objects: ClassVar[dict[str, bytes]] = {}
    deleted: ClassVar[list[str]] = []
    next_key = 0

    def __init__(self) -> None:
        pass

    def upload(self, content: BytesIO) -> str:
        self.__class__.next_key += 1
        key = f"documents/evidence-{self.__class__.next_key}"
        if key in self.__class__.objects:
            raise AssertionError("Object keys must be immutable")
        self.__class__.objects[key] = content.read()
        return key

    def download(self, object_key: str) -> BytesIO:
        return BytesIO(self.__class__.objects[object_key])

    def delete(self, object_key: str) -> None:
        self.__class__.deleted.append(object_key)
        self.__class__.objects.pop(object_key, None)


async def _reset_evidence_file_data() -> UUID:
    async with async_session() as session:
        await session.execute(delete(DocumentEvidenceLink))
        await session.execute(delete(EvidenceItem))
        await session.execute(delete(UserSession))
        await session.execute(delete(User))
        user = User(
            email="evidence-file-reviewer@neudive.com",
            display_name="근거 파일 검토자",
            password_hash=hash_password("correct-horse-battery-staple"),
        )
        session.add(user)
        await session.commit()
        return user.id


@pytest.fixture
def authenticated_client(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient]:
    asyncio.run(_reset_evidence_file_data())
    FakeObjectStorage.objects = {}
    FakeObjectStorage.deleted = []
    FakeObjectStorage.next_key = 0
    monkeypatch.setattr("ide_api.domains.evidence.service.ObjectStorage", FakeObjectStorage)
    monkeypatch.setattr(
        "ide_api.domains.evidence.service.get_settings",
        lambda: SimpleNamespace(max_upload_size_bytes=4 * 1024 * 1024),
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "evidence-file-reviewer@neudive.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 200
    yield client
    asyncio.run(_reset_evidence_file_data())


def test_evidence_files_preserve_binary_content_and_hide_storage_key(
    authenticated_client: TestClient,
) -> None:
    image = b"\x89PNG\r\n\x1a\nimage-content"
    image_response = authenticated_client.post(
        "/api/v1/evidence/files",
        data={"title": "Screenshot", "description": "Captured screen", "version": "1"},
        files={"file": ("screen.png", image, "image/png")},
    )
    assert image_response.status_code == 201
    image_item = image_response.json()
    assert "object_key" not in image_item

    report = b"ordinary text file\n"
    report_response = authenticated_client.post(
        "/api/v1/evidence/files",
        data={"title": "Report", "description": "Captured report"},
        files={"file": ("report.txt", report, "text/plain")},
    )
    assert report_response.status_code == 201
    assert "object_key" not in report_response.json()

    download_response = authenticated_client.get(f"/api/v1/evidence/{image_item['id']}/file")
    assert download_response.status_code == 200
    assert download_response.content == image
    assert download_response.headers["content-type"] == "image/png"
    assert "attachment;" in download_response.headers["content-disposition"]
    assert (
        hashlib.sha256(image).hexdigest() == hashlib.sha256(download_response.content).hexdigest()
    )


def test_evidence_file_rejects_empty_and_oversized_uploads(
    authenticated_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty_response = authenticated_client.post(
        "/api/v1/evidence/files",
        data={"title": "Empty", "description": "No content"},
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert empty_response.status_code == 422

    monkeypatch.setattr(
        "ide_api.domains.evidence.service.get_settings",
        lambda: SimpleNamespace(max_upload_size_bytes=3),
    )
    oversized_response = authenticated_client.post(
        "/api/v1/evidence/files",
        data={"title": "Large", "description": "Too large"},
        files={"file": ("large.txt", b"1234", "text/plain")},
    )
    assert oversized_response.status_code == 422
    assert FakeObjectStorage.objects == {}


def test_evidence_file_download_rejects_metadata_items_and_unauthenticated_requests(
    authenticated_client: TestClient,
) -> None:
    metadata_response = authenticated_client.post(
        "/api/v1/evidence/items",
        json={
            "evidence_type": "test_result",
            "title": "Metadata only",
            "description": "No uploaded file",
        },
    )
    assert metadata_response.status_code == 201
    assert (
        authenticated_client.get(
            f"/api/v1/evidence/{metadata_response.json()['id']}/file"
        ).status_code
        == 404
    )

    unauthenticated_client = TestClient(authenticated_client.app, base_url="https://testserver")
    try:
        response = unauthenticated_client.post(
            "/api/v1/evidence/files",
            data={"title": "Blocked", "description": "Blocked upload"},
            files={"file": ("blocked.txt", b"data", "text/plain")},
        )
        assert response.status_code == 401
    finally:
        unauthenticated_client.close()
