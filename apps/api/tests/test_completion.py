import asyncio
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from io import BytesIO
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from ide_api.cmd.api import app
from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.approvals.models import ApprovalStep, ApprovalWorkflow
from ide_api.domains.auth.models import User
from ide_api.domains.changes.models import ChangeProposal, ChangeRequest
from ide_api.domains.completion import router as completion_router
from ide_api.domains.documents.models import Document
from ide_api.domains.evidence.models import DocumentEvidenceLink, EvidenceItem
from ide_api.domains.impacts.models import DocumentImpact, DocumentRelationship
from ide_api.domains.latex.models import LatexRevision


class MemoryStorage:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = objects
        self.downloaded_keys: list[str] = []

    def download(self, object_key: str) -> BytesIO:
        self.downloaded_keys.append(object_key)
        return BytesIO(self.objects[object_key])


async def _reset_completion_data() -> None:
    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        await session.commit()


async def _create_document(
    *,
    user_id: UUID,
    object_key: str,
    pdf: bytes | None = b"compiled PDF",
    conversion_status: str = "not_required",
    compile_status: str = "succeeded",
    with_open_gates: bool = False,
) -> tuple[UUID, UUID]:
    async with async_session() as session:
        document = Document(id=uuid4())
        revision = LatexRevision(
            id=uuid4(),
            document_id=document.id,
            source_object_key=f"private/source-{uuid4()}.zip",
            source_sha256="0" * 64,
            entrypoint="main.tex",
            origin="latex_upload",
            conversion_status=conversion_status,
            compile_status=compile_status,
            compiled_pdf_object_key=object_key if pdf is not None else None,
            compiled_pdf_sha256=sha256(pdf).hexdigest() if pdf is not None else None,
            created_by_id=user_id,
        )
        workflow = ApprovalWorkflow(
            id=uuid4(),
            document_id=document.id,
            status="pending" if with_open_gates else "completed",
            is_started=True,
        )
        step = ApprovalStep(
            id=uuid4(),
            workflow_id=workflow.id,
            name="Approval",
            assignee_id=user_id,
            sequence=1,
            status="current" if with_open_gates else "completed",
        )
        session.add_all([document, revision, workflow, step])
        if with_open_gates:
            request = ChangeRequest(
                id=uuid4(),
                document_id=document.id,
                requester_id=user_id,
                title="Open request",
                description="Needs review",
                status="open",
            )
            proposal = ChangeProposal(
                id=uuid4(),
                change_request_id=request.id,
                proposed_text="Candidate",
                rationale="Review",
                status="candidate",
            )
            relationship = DocumentRelationship(
                id=uuid4(),
                source_document_id=document.id,
                source_location="1",
                target_document_id=document.id,
                target_location="2",
                relationship_type="reference",
                reason="Candidate",
                status="candidate",
            )
            impact = DocumentImpact(
                id=uuid4(),
                source_document_id=document.id,
                source_location="1",
                target_document_id=document.id,
                target_location="2",
                reason="Candidate",
                proposed_modification="Review",
                status="candidate",
            )
            evidence = EvidenceItem(
                id=uuid4(), evidence_type="reference", title="Evidence", description="Source"
            )
            evidence_link = DocumentEvidenceLink(
                id=uuid4(),
                document_id=document.id,
                evidence_id=evidence.id,
                status="candidate",
                freshness="stale",
                reason="Candidate",
            )
            session.add_all([request, proposal, relationship, impact, evidence, evidence_link])
        await session.commit()
        return document.id, revision.id


async def _create_user(email: str) -> UUID:
    async with async_session() as session:
        user = User(
            email=email,
            display_name="Completer",
            password_hash=hash_password("password"),
        )
        session.add(user)
        await session.commit()
        return user.id


@pytest.fixture
def completion_client(client: TestClient) -> tuple[TestClient, MemoryStorage]:
    asyncio.run(_reset_completion_data())
    storage = MemoryStorage(
        {
            "private/native.pdf": b"native compiled PDF",
            "private/accepted.pdf": b"accepted compiled PDF",
            "private/gated.pdf": b"gated compiled PDF",
            "private/pending.pdf": b"pending conversion PDF",
            "private/failed.pdf": b"failed compile PDF",
            "private/stale.pdf": b"stale compiled PDF",
            "private/latest.pdf": b"latest compiled PDF",
            "private/other.pdf": b"other compiled PDF",
        }
    )
    app.dependency_overrides[completion_router._storage] = lambda: storage
    try:
        yield client, storage
    finally:
        app.dependency_overrides.pop(completion_router._storage, None)


def _codes(response: object) -> set[str]:
    return {reason["code"] for reason in response.json()["blocking_reasons"]}  # type: ignore[attr-defined]


def test_completion_requires_reviewed_latest_compiled_latex(
    completion_client: tuple[TestClient, MemoryStorage],
) -> None:
    client, storage = completion_client
    email = f"completion-{uuid4()}@example.com"
    user_id = asyncio.run(_create_user(email))

    native_document_id, native_revision_id = asyncio.run(
        _create_document(
            user_id=user_id,
            object_key="private/native.pdf",
            pdf=b"native compiled PDF",
        )
    )
    native_payload = {
        "document_id": str(native_document_id),
        "latex_revision_id": str(native_revision_id),
    }
    assert client.post("/api/v1/completion/evaluate", json=native_payload).status_code == 401
    assert (
        client.post("/api/v1/auth/login", json={"email": email, "password": "password"}).status_code
        == 200
    )

    missing_revision = client.post(
        "/api/v1/completion/evaluate",
        json={"document_id": str(native_document_id), "latex_revision_id": str(uuid4())},
    )
    assert _codes(missing_revision) == {"latex_revision_not_found"}

    gated_document_id, gated_revision_id = asyncio.run(
        _create_document(user_id=user_id, object_key="private/gated.pdf", with_open_gates=True)
    )
    gated = client.post(
        "/api/v1/completion/evaluate",
        json={"document_id": str(gated_document_id), "latex_revision_id": str(gated_revision_id)},
    )
    assert {
        "pending_change_requests",
        "pending_change_proposals",
        "pending_relationship_candidates",
        "pending_impact_candidates",
        "pending_evidence_candidates",
        "stale_evidence",
        "approval_steps_incomplete",
    } <= _codes(gated)
    assert (
        client.post(
            "/api/v1/completion",
            json={
                "document_id": str(gated_document_id),
                "latex_revision_id": str(gated_revision_id),
            },
        ).status_code
        == 409
    )

    pending_document_id, pending_revision_id = asyncio.run(
        _create_document(
            user_id=user_id,
            object_key="private/pending.pdf",
            conversion_status="pending_review",
        )
    )
    pending = client.post(
        "/api/v1/completion/evaluate",
        json={
            "document_id": str(pending_document_id),
            "latex_revision_id": str(pending_revision_id),
        },
    )
    assert _codes(pending) == {"conversion_review_pending"}

    failed_document_id, failed_revision_id = asyncio.run(
        _create_document(
            user_id=user_id,
            object_key="private/failed.pdf",
            compile_status="failed",
        )
    )
    failed = client.post(
        "/api/v1/completion/evaluate",
        json={"document_id": str(failed_document_id), "latex_revision_id": str(failed_revision_id)},
    )
    assert _codes(failed) == {"compile_failed"}

    compiling_document_id, compiling_revision_id = asyncio.run(
        _create_document(
            user_id=user_id,
            object_key="private/compiling.pdf",
            compile_status="pending",
        )
    )
    compiling = client.post(
        "/api/v1/completion/evaluate",
        json={
            "document_id": str(compiling_document_id),
            "latex_revision_id": str(compiling_revision_id),
        },
    )
    assert _codes(compiling) == {"compile_incomplete"}

    missing_pdf_document_id, missing_pdf_revision_id = asyncio.run(
        _create_document(user_id=user_id, object_key="private/missing.pdf", pdf=None)
    )
    missing_pdf = client.post(
        "/api/v1/completion/evaluate",
        json={
            "document_id": str(missing_pdf_document_id),
            "latex_revision_id": str(missing_pdf_revision_id),
        },
    )
    assert _codes(missing_pdf) == {"compiled_pdf_missing"}

    rejected_document_id, rejected_revision_id = asyncio.run(
        _create_document(
            user_id=user_id,
            object_key="private/rejected.pdf",
            conversion_status="rejected",
        )
    )
    rejected = client.post(
        "/api/v1/completion/evaluate",
        json={
            "document_id": str(rejected_document_id),
            "latex_revision_id": str(rejected_revision_id),
        },
    )
    assert _codes(rejected) == {"conversion_rejected"}

    stale_document_id, stale_revision_id = asyncio.run(
        _create_document(user_id=user_id, object_key="private/stale.pdf")
    )

    async def add_latest() -> UUID:
        async with async_session() as session:
            revision = LatexRevision(
                id=uuid4(),
                document_id=stale_document_id,
                source_object_key=f"private/source-{uuid4()}.zip",
                source_sha256="1" * 64,
                entrypoint="main.tex",
                origin="web_edit",
                conversion_status="not_required",
                compile_status="succeeded",
                compiled_pdf_object_key="private/latest.pdf",
                compiled_pdf_sha256=sha256(b"latest compiled PDF").hexdigest(),
                created_by_id=user_id,
                created_at=datetime.now(UTC) + timedelta(seconds=1),
            )
            session.add(revision)
            await session.commit()
            return revision.id

    asyncio.run(add_latest())
    stale = client.post(
        "/api/v1/completion/evaluate",
        json={"document_id": str(stale_document_id), "latex_revision_id": str(stale_revision_id)},
    )
    assert _codes(stale) == {"latex_revision_not_latest"}

    other_document_id, other_revision_id = asyncio.run(
        _create_document(user_id=user_id, object_key="private/other.pdf")
    )
    assert other_document_id != native_document_id
    mismatch = client.post(
        "/api/v1/completion/evaluate",
        json={"document_id": str(native_document_id), "latex_revision_id": str(other_revision_id)},
    )
    assert _codes(mismatch) == {"latex_revision_document_mismatch"}

    completed = client.post("/api/v1/completion", json=native_payload)
    assert completed.status_code == 201
    assert completed.json()["latex_revision_id"] == str(native_revision_id)
    assert completed.json()["compiled_pdf_sha256"] == sha256(b"native compiled PDF").hexdigest()
    assert client.post("/api/v1/completion", json=native_payload).status_code == 409

    exported = client.get(f"/api/v1/completion/documents/{native_document_id}/export")
    assert exported.status_code == 200
    assert exported.content == b"native compiled PDF"
    assert exported.headers["content-type"].startswith("application/pdf")
    assert f"{native_document_id}.pdf" in exported.headers["content-disposition"]
    assert "private/native.pdf" not in str(dict(exported.headers))
    assert storage.downloaded_keys == ["private/native.pdf"]

    storage.objects["private/native.pdf"] = b"corrupt PDF"
    assert (
        client.get(f"/api/v1/completion/documents/{native_document_id}/export").status_code == 503
    )

    accepted_document_id, accepted_revision_id = asyncio.run(
        _create_document(
            user_id=user_id,
            object_key="private/accepted.pdf",
            conversion_status="accepted",
        )
    )
    assert (
        client.post(
            "/api/v1/completion",
            json={
                "document_id": str(accepted_document_id),
                "latex_revision_id": str(accepted_revision_id),
            },
        ).status_code
        == 201
    )
