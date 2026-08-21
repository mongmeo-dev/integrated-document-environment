import asyncio
from collections.abc import Generator
from io import BytesIO
from typing import ClassVar

import pytest
from docx import Document as DocxDocument
from fastapi.testclient import TestClient
from sqlalchemy import text

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User
from ide_api.domains.completion import router as completion_router
from ide_api.domains.documents import router as documents_router
from ide_api.domains.latex.bundle import build_single_file_bundle
from ide_api.domains.latex.compilation import LatexCompilationResult, TectonicCompiler
from ide_api.domains.latex.conversion import PandocDocxConverter

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PASSWORD = "phase1-password"
AUTHOR_EMAIL = "phase1-author@example.com"
APPROVER_EMAIL = "phase1-approver@example.com"
COMPILED_PDF = b"%PDF-1.7\nPhase 1 compiled PDF\n"


class FakeObjectStorage:
    objects: ClassVar[dict[str, bytes]] = {}

    def upload(self, content: object) -> str:
        key = f"test/{len(self.objects) + 1}"
        self.objects[key] = content.read()
        return key

    def download(self, object_key: str) -> BytesIO:
        return BytesIO(self.objects[object_key])

    def delete(self, object_key: str) -> None:
        self.objects.pop(object_key, None)


async def _seed_users() -> tuple[str, str]:
    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        author = User(
            email=AUTHOR_EMAIL,
            display_name="Phase 1 Author",
            password_hash=hash_password(PASSWORD),
        )
        approver = User(
            email=APPROVER_EMAIL,
            display_name="Phase 1 Approver",
            password_hash=hash_password(PASSWORD),
        )
        session.add_all([author, approver])
        await session.commit()
        return str(author.id), str(approver.id)


async def _complete_relationship_analysis(document_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            text(
                "UPDATE relationship_analysis_runs "
                "SET status = 'completed', model_id = 'test-model', completed_at = now() "
                "WHERE source_document_id = :document_id"
            ),
            {"document_id": document_id},
        )
        await session.commit()


@pytest.fixture
def phase1_client(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> Generator[tuple[TestClient, str, str]]:
    FakeObjectStorage.objects = {}
    author_id, approver_id = asyncio.run(_seed_users())
    storage = FakeObjectStorage()
    client.app.dependency_overrides[documents_router.get_object_storage] = lambda: storage
    client.app.dependency_overrides[completion_router._storage] = lambda: storage
    monkeypatch.setattr(
        PandocDocxConverter,
        "convert",
        lambda _self, _content: build_single_file_bundle(
            b"\\documentclass{article}\n\\begin{document}Phase 1 document\\end{document}\n"
        ),
    )
    monkeypatch.setattr(
        TectonicCompiler,
        "compile",
        lambda _self, _bundle: LatexCompilationResult(
            pdf=COMPILED_PDF,
            log="compiled",
        ),
    )
    yield client, author_id, approver_id
    client.app.dependency_overrides.pop(documents_router.get_object_storage, None)
    client.app.dependency_overrides.pop(completion_router._storage, None)


def _docx_bytes() -> bytes:
    document = DocxDocument()
    document.add_paragraph("Phase 1 document")
    content = BytesIO()
    document.save(content)
    return content.getvalue()


def _login(client: TestClient, email: str) -> None:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200


def test_phase1_internal_docx_journey_over_http(
    phase1_client: tuple[TestClient, str, str],
) -> None:
    client, author_id, approver_id = phase1_client
    _login(client, AUTHOR_EMAIL)

    source = _docx_bytes()
    registered = client.post(
        "/api/v1/documents",
        files={"file": ("phase1.docx", source, DOCX_MEDIA_TYPE)},
    )
    assert registered.status_code == 202
    document = registered.json()
    document_id = document["id"]
    assert document["creator"]["id"] == author_id

    listed = client.get("/api/v1/documents", params={"query": "phase1"})
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [document_id]

    validated = client.post(f"/api/v1/documents/{document_id}/validate")
    assert validated.status_code == 200
    assert validated.json()["status"] == "ready"
    analysis = client.get(f"/api/v1/impacts/documents/{document_id}/analysis")
    assert analysis.status_code == 200
    assert analysis.json()["status"] == "queued"
    asyncio.run(_complete_relationship_analysis(document_id))
    project = client.get(f"/api/v1/documents/{document_id}/latex")
    assert project.status_code == 200
    revision_id = project.json()["revision_id"]
    assert project.json()["conversion_status"] == "pending_review"
    reviewed = client.post(
        f"/api/v1/documents/{document_id}/latex/conversion-reviews",
        json={
            "expected_revision_id": revision_id,
            "decision": "accepted",
            "reason": "원본 DOCX와 변환된 LaTeX 및 컴파일 PDF를 검토했습니다.",
        },
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["conversion_status"] == "accepted"

    change = client.post(
        "/api/v1/changes",
        json={
            "document_id": document_id,
            "title": "Clarify retention",
            "description": "Clarify the document retention period.",
        },
    )
    assert change.status_code == 201
    change_id = change.json()["id"]
    assert change.json()["requester_id"] == author_id
    assert (
        client.patch(
            f"/api/v1/changes/{change_id}/status", json={"status": "in_review"}
        ).status_code
        == 200
    )
    proposal = client.post(
        f"/api/v1/changes/{change_id}/proposals",
        json={
            "proposed_text": "Retain records for seven years.",
            "rationale": "Policy requirement.",
        },
    )
    assert proposal.status_code == 201
    proposal_id = proposal.json()["id"]
    proposal_decision = client.patch(
        f"/api/v1/changes/{change_id}/proposals/{proposal_id}/decision",
        json={"status": "accepted"},
    )
    assert proposal_decision.status_code == 200
    assert proposal_decision.json()["decided_by_id"] == author_id
    assert proposal_decision.json()["decided_at"] is not None
    accepted_change = client.patch(
        f"/api/v1/changes/{change_id}/status", json={"status": "accepted"}
    )
    assert accepted_change.status_code == 200

    relationship = client.post(
        "/api/v1/impacts/relationships",
        json={
            "source_document_id": document_id,
            "source_location": "paragraph:1",
            "target_document_id": document_id,
            "target_location": "paragraph:1",
            "relationship_type": "semantic",
            "reason": "The revised requirement changes the policy statement.",
        },
    )
    assert relationship.status_code == 201
    relationship_decision = client.patch(
        f"/api/v1/impacts/relationships/{relationship.json()['id']}/confirm"
    )
    assert relationship_decision.status_code == 200
    assert relationship_decision.json()["decided_by_id"] == author_id
    assert relationship_decision.json()["decided_at"] is not None

    impact = client.post(
        "/api/v1/impacts/candidates",
        json={
            "source_document_id": document_id,
            "source_location": "paragraph:1",
            "target_document_id": document_id,
            "target_location": "paragraph:1",
            "reason": "The policy matrix must reflect the new retention period.",
            "proposed_modification": "Set retention to seven years.",
        },
    )
    assert impact.status_code == 201
    impact_id = impact.json()["id"]
    impact_decision = client.patch(f"/api/v1/impacts/candidates/{impact_id}/confirm")
    assert impact_decision.status_code == 200
    assert impact_decision.json()["decided_by_id"] == author_id
    assert impact_decision.json()["decided_at"] is not None
    modification_decision = client.patch(
        f"/api/v1/impacts/candidates/{impact_id}/modification-required"
    )
    assert modification_decision.status_code == 200
    assert modification_decision.json()["modification_decided_by_id"] == author_id
    assert modification_decision.json()["modification_decided_at"] is not None

    evidence = client.post(
        "/api/v1/evidence/items",
        json={
            "evidence_type": "test_result",
            "title": "Phase 1 verification",
            "description": "The end-to-end API journey passed.",
            "reference": "phase1-journey",
        },
    )
    assert evidence.status_code == 201
    evidence_link = client.post(
        "/api/v1/evidence/links",
        json={
            "document_id": document_id,
            "evidence_id": evidence.json()["id"],
            "reason": "This test verifies the approved document result.",
        },
    )
    assert evidence_link.status_code == 201
    link_id = evidence_link.json()["id"]
    evidence_decision = client.patch(f"/api/v1/evidence/links/{link_id}/confirm")
    assert evidence_decision.status_code == 200
    assert evidence_decision.json()["decided_by_id"] == author_id
    assert evidence_decision.json()["decided_at"] is not None
    assert (
        client.patch(f"/api/v1/evidence/items/{evidence.json()['id']}/links/stale").status_code
        == 204
    )
    freshness_review = client.patch(f"/api/v1/evidence/links/{link_id}/freshness-review")
    assert freshness_review.status_code == 200
    assert freshness_review.json()["freshness"] == "current"
    assert freshness_review.json()["reviewed_by_id"] == author_id
    assert freshness_review.json()["reviewed_at"] is not None

    workflow = client.post(
        "/api/v1/approvals",
        json={
            "document_id": document_id,
            "steps": [
                {"name": "Author review", "assignee_id": author_id, "sequence": 1},
                {"name": "Approval review", "assignee_id": approver_id, "sequence": 2},
            ],
        },
    )
    assert workflow.status_code == 201
    workflow_id = workflow.json()["id"]
    first_step, second_step = workflow.json()["steps"]
    started = client.post(f"/api/v1/approvals/{workflow_id}/start")
    assert started.status_code == 200
    assert started.json()["started_at"] is not None
    assert started.json()["steps"][0]["status"] == "current"
    first_approval = client.post(f"/api/v1/approvals/steps/{first_step['id']}/approve")
    assert first_approval.status_code == 200
    assert first_approval.json()["steps"][0]["completed_at"] is not None
    assert first_approval.json()["steps"][1]["status"] == "current"
    _login(client, APPROVER_EMAIL)
    second_approval = client.post(f"/api/v1/approvals/steps/{second_step['id']}/approve")
    assert second_approval.status_code == 200
    assert second_approval.json()["completed_at"] is not None
    assert second_approval.json()["steps"][1]["assignee_id"] == approver_id

    completion_payload = {
        "document_id": document_id,
        "latex_revision_id": revision_id,
    }
    evaluated = client.post("/api/v1/completion/evaluate", json=completion_payload)
    assert evaluated.status_code == 200
    assert evaluated.json()["blocking_reasons"] == []
    completed = client.post("/api/v1/completion", json=completion_payload)
    assert completed.status_code == 201
    assert completed.json()["completed_by_id"] == approver_id
    assert completed.json()["completed_at"] is not None
    exported = client.get(f"/api/v1/completion/documents/{document_id}/export")
    assert exported.status_code == 200
    assert exported.content == COMPILED_PDF
    assert source in FakeObjectStorage.objects.values()
