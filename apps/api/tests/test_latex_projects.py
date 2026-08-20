import asyncio
import hashlib
from collections.abc import Generator
from io import BytesIO
from typing import ClassVar
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from ide_api.cmd.api import app
from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User
from ide_api.domains.documents import router as documents_router
from ide_api.domains.latex.bundle import build_single_file_bundle, read_latex_bundle
from ide_api.domains.latex.compilation import (
    LatexCompilationError,
    LatexCompilationResult,
    TectonicCompiler,
)
from ide_api.domains.latex.conversion import PandocDocxConverter

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TEX_MEDIA_TYPE = "text/x-tex"
PDF_BYTES = b"%PDF-1.7\nlatex-preview\n"


class FakeObjectStorage:
    objects: ClassVar[dict[str, bytes]] = {}

    def upload(self, content: object) -> str:
        key = f"test-object/{len(self.objects) + 1}"
        self.objects[key] = content.read()
        return key

    def download(self, object_key: str) -> BytesIO:
        return BytesIO(self.objects[object_key])

    def delete(self, object_key: str) -> None:
        self.objects.pop(object_key, None)


async def _reset_latex_project_data() -> None:
    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        session.add(
            User(
                email="latex-projects@example.com",
                display_name="LaTeX Project Tester",
                password_hash=hash_password("latex-project-password"),
            )
        )
        await session.commit()


@pytest.fixture(autouse=True)
def latex_project_data(client: TestClient) -> Generator[FakeObjectStorage]:
    FakeObjectStorage.objects = {}
    asyncio.run(_reset_latex_project_data())
    storage = FakeObjectStorage()
    app.dependency_overrides[documents_router.get_object_storage] = lambda: storage
    yield storage
    app.dependency_overrides.pop(documents_router.get_object_storage, None)
    FakeObjectStorage.objects = {}


@pytest.fixture
def successful_processors(monkeypatch: pytest.MonkeyPatch) -> None:
    def convert(_: PandocDocxConverter, __: bytes):
        return build_single_file_bundle(
            b"\\documentclass{article}\n\\begin{document}Converted\\end{document}\n"
        )

    def compile(_: TectonicCompiler, __: object) -> LatexCompilationResult:
        return LatexCompilationResult(pdf=PDF_BYTES, log="compiled successfully")

    monkeypatch.setattr(PandocDocxConverter, "convert", convert)
    monkeypatch.setattr(TectonicCompiler, "compile", compile)


def test_native_latex_project_keeps_original_immutable_and_supports_revisions(
    client: TestClient, successful_processors: None, latex_project_data: FakeObjectStorage
) -> None:
    _login(client)
    original = b"\\documentclass{article}\n\\begin{document}Original\\end{document}\n"
    document = _register(client, "main.tex", original)
    document_id = document["id"]
    original_object = dict(latex_project_data.objects)

    validated = client.post(f"/api/v1/documents/{document_id}/validate")
    assert validated.status_code == 200
    assert validated.json()["status"] == "ready"

    project = client.get(f"/api/v1/documents/{document_id}/latex")
    assert project.status_code == 200
    first = project.json()
    assert first["origin"] == "latex_upload"
    assert first["conversion_status"] == "not_required"
    assert first["compile_status"] == "succeeded"
    assert first["source"] == original.decode()
    assert first["source_sha256"] == build_single_file_bundle(original, "main.tex").sha256
    assert first["compiled_pdf_sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    assert first["preview_available"] is True
    assert "object_key" not in project.text
    assert "source_object_key" not in project.text
    assert "compiled_pdf_object_key" not in project.text

    preview = client.get(f"/api/v1/documents/{document_id}/latex/preview")
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "application/pdf"
    assert preview.content == PDF_BYTES

    bundle_response = client.get(f"/api/v1/documents/{document_id}/latex/bundle")
    assert bundle_response.status_code == 200
    assert read_latex_bundle(bundle_response.content).source == original.decode()

    updated_source = "\\documentclass{article}\n\\begin{document}Updated\\end{document}\n"
    created = client.post(
        f"/api/v1/documents/{document_id}/latex/revisions",
        json={"expected_revision_id": first["revision_id"], "source": updated_source},
    )
    assert created.status_code == 201
    second = created.json()
    assert second["revision_id"] != first["revision_id"]
    assert second["origin"] == "web_edit"
    assert second["source"] == updated_source

    stale = client.post(
        f"/api/v1/documents/{document_id}/latex/revisions",
        json={"expected_revision_id": first["revision_id"], "source": original.decode()},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "stale_revision"
    original_key = next(iter(original_object))
    assert latex_project_data.objects[original_key] == original


def test_docx_conversion_requires_explicit_review(
    client: TestClient, successful_processors: None
) -> None:
    _login(client)
    document = _register(client, "import.docx", _docx_bytes())
    document_id = document["id"]

    validated = client.post(f"/api/v1/documents/{document_id}/validate")
    assert validated.status_code == 200
    project = client.get(f"/api/v1/documents/{document_id}/latex")
    assert project.status_code == 200
    pending = project.json()
    assert pending["origin"] == "docx_conversion"
    assert pending["conversion_status"] == "pending_review"
    assert pending["compile_status"] == "succeeded"
    assert pending["compiled_pdf_sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()

    blank_reason = client.post(
        f"/api/v1/documents/{document_id}/latex/conversion-reviews",
        json={
            "expected_revision_id": pending["revision_id"],
            "decision": "accepted",
            "reason": "   ",
        },
    )
    assert blank_reason.status_code == 422

    accepted = client.post(
        f"/api/v1/documents/{document_id}/latex/conversion-reviews",
        json={
            "expected_revision_id": pending["revision_id"],
            "decision": "accepted",
            "reason": "Verified converted content.",
        },
    )
    assert accepted.status_code == 200
    assert accepted.json()["conversion_status"] == "accepted"

    second_decision = client.post(
        f"/api/v1/documents/{document_id}/latex/conversion-reviews",
        json={
            "expected_revision_id": pending["revision_id"],
            "decision": "rejected",
            "reason": "Attempting a second decision.",
        },
    )
    assert second_decision.status_code == 409
    assert second_decision.json()["detail"]["code"] == "invalid_conversion_transition"

    edited = client.post(
        f"/api/v1/documents/{document_id}/latex/revisions",
        json={
            "expected_revision_id": pending["revision_id"],
            "source": "\\documentclass{article}\n\\begin{document}Reviewed edit\\end{document}\n",
        },
    )
    assert edited.status_code == 201
    assert edited.json()["origin"] == "web_edit"
    assert edited.json()["conversion_status"] == "pending_review"


def test_compiler_failure_keeps_validated_original_and_disables_preview(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, latex_project_data: FakeObjectStorage
) -> None:
    def compile_failure(_: TectonicCompiler, __: object) -> LatexCompilationResult:
        raise LatexCompilationError("compilation_failed", "Compilation failed.", "missing package")

    monkeypatch.setattr(TectonicCompiler, "compile", compile_failure)
    _login(client)
    original = b"\\documentclass{article}\n\\begin{document}Failure\\end{document}\n"
    document = _register(client, "failure.tex", original)
    document_id = document["id"]

    validated = client.post(f"/api/v1/documents/{document_id}/validate")
    assert validated.status_code == 200
    assert validated.json()["status"] == "ready"
    project = client.get(f"/api/v1/documents/{document_id}/latex")
    assert project.status_code == 200
    assert project.json()["compile_status"] == "failed"
    assert project.json()["compile_log"] == "missing package"
    assert project.json()["preview_available"] is False
    preview = client.get(f"/api/v1/documents/{document_id}/latex/preview")
    assert preview.status_code == 422
    assert preview.json()["detail"]["code"] == "preview_unavailable"
    assert any(data == original for data in latex_project_data.objects.values())


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/api/v1/documents/00000000-0000-0000-0000-000000000000/latex", None),
        ("get", "/api/v1/documents/00000000-0000-0000-0000-000000000000/latex/preview", None),
        ("get", "/api/v1/documents/00000000-0000-0000-0000-000000000000/latex/bundle", None),
        (
            "post",
            "/api/v1/documents/00000000-0000-0000-0000-000000000000/latex/revisions",
            {"expected_revision_id": "00000000-0000-0000-0000-000000000000", "source": "x"},
        ),
        (
            "post",
            "/api/v1/documents/00000000-0000-0000-0000-000000000000/latex/conversion-reviews",
            {
                "expected_revision_id": "00000000-0000-0000-0000-000000000000",
                "decision": "accepted",
                "reason": "Reviewed.",
            },
        ),
    ],
)
def test_latex_endpoints_require_authentication(
    client: TestClient, method: str, path: str, json: dict[str, str] | None
) -> None:
    response = client.request(method, path, json=json)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "authentication_required"


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "latex-projects@example.com", "password": "latex-project-password"},
    )
    assert response.status_code == 200


def _register(client: TestClient, filename: str, content: bytes) -> dict[str, object]:
    media_type = TEX_MEDIA_TYPE if filename.endswith(".tex") else DOCX_MEDIA_TYPE
    response = client.post("/api/v1/documents", files={"file": (filename, content, media_type)})
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
