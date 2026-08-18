import asyncio
from io import BytesIO
from typing import ClassVar
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User
from ide_api.domains.documents import router as documents_router

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class FakeObjectStorage:
    objects: ClassVar[dict[str, bytes]] = {}

    def upload(self, content: object) -> str:
        key = f"original/{len(self.objects) + 1}"
        self.objects[key] = content.read()
        return key

    def download(self, object_key: str) -> BytesIO:
        return BytesIO(self.objects[object_key])

    def delete(self, object_key: str) -> None:
        self.objects.pop(object_key, None)


async def _reset_data() -> None:
    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        session.add(
            User(
                email="documents@example.com",
                display_name="Document Tester",
                password_hash=hash_password("document-password"),
            )
        )
        await session.commit()


@pytest.fixture(autouse=True)
def document_data(client: TestClient) -> None:
    FakeObjectStorage.objects = {}
    asyncio.run(_reset_data())
    client.app.dependency_overrides[documents_router.get_object_storage] = FakeObjectStorage
    yield
    client.app.dependency_overrides.pop(documents_router.get_object_storage, None)


def test_register_list_and_validate_ready_document(client: TestClient) -> None:
    _login(client)
    registered = _register(client, "quality-plan.docx", _docx_bytes())
    document_id = registered["id"]

    listed = client.get(
        "/api/v1/documents",
        params={"query": "QUALITY", "status": "queued", "limit": 1, "offset": 0},
    )
    assert listed.status_code == 200
    assert [document["id"] for document in listed.json()] == [document_id]
    assert "object_key" not in listed.text

    validated = client.post(f"/api/v1/documents/{document_id}/validate")
    assert validated.status_code == 200
    assert validated.json()["status"] == "ready"
    assert validated.json()["input_kind"] == "editable_docx"
    assert validated.json()["capabilities"] == {
        "analysis": True,
        "external_edit_round_trip": True,
        "format_comparison": True,
        "approved_output": True,
    }
    assert "object_key" not in validated.text


def test_validate_rejects_corrupt_document_with_reason(client: TestClient) -> None:
    _login(client)
    registered = _register(client, "broken.docx", b"not a docx archive")

    validated = client.post(f"/api/v1/documents/{registered['id']}/validate")
    assert validated.status_code == 200
    assert validated.json()["status"] == "rejected"
    assert validated.json()["rejection"]["code"] == "corrupt_document"
    assert validated.json()["rejection"]["message"]
    assert "object_key" not in validated.text


def test_document_list_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/documents")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "authentication_required"


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "documents@example.com", "password": "document-password"},
    )
    assert response.status_code == 200


def _register(client: TestClient, filename: str, content: bytes) -> dict[str, object]:
    response = client.post(
        "/api/v1/documents",
        files={"file": (filename, content, DOCX_MEDIA_TYPE)},
    )
    assert response.status_code == 202
    return response.json()


def _docx_bytes() -> bytes:
    content = BytesIO()
    with ZipFile(content, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                b'<?xml version="1.0" encoding="UTF-8"?>'
                b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                b'<Override PartName="/word/document.xml" '
                b'ContentType="application/vnd.openxmlformats-officedocument.'
                b'wordprocessingml.document.main+xml"/>'
                b"</Types>"
            ),
        )
        archive.writestr(
            "word/document.xml",
            b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            b"<w:body/></w:document>",
        )
    return content.getvalue()
