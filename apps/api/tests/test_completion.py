import asyncio
from io import BytesIO
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from ide_api.cmd.api import app
from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.approvals.models import ApprovalStep, ApprovalWorkflow
from ide_api.domains.auth.models import User
from ide_api.domains.changes.models import ChangeProposal, ChangeRequest
from ide_api.domains.completion import router as completion_router
from ide_api.domains.documents.models import Document, DocumentVersion
from ide_api.domains.evidence.models import DocumentEvidenceLink, EvidenceItem
from ide_api.domains.formatting.models import ExternalEditResult, FormatCheck
from ide_api.domains.impacts.models import DocumentImpact, DocumentRelationship


class MemoryStorage:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = objects
        self.downloaded_keys: list[str] = []

    def download(self, object_key: str) -> BytesIO:
        self.downloaded_keys.append(object_key)
        return BytesIO(self.objects[object_key])


async def _create_document(
    *,
    user_id: UUID,
    input_kind: str,
    original_format: str,
    filename: str,
    media_type: str,
    object_key: str,
    with_open_gates: bool = False,
) -> tuple[UUID, UUID]:
    async with async_session() as session:
        document = Document(id=uuid4())
        version = DocumentVersion(
            id=uuid4(),
            document_id=document.id,
            original_filename=filename,
            media_type=media_type,
            size_bytes=1,
            sha256="0" * 64,
            object_key=f"source-{uuid4()}",
            created_by_id=user_id,
            input_kind=input_kind,
        )
        result = ExternalEditResult(
            id=uuid4(),
            document_id=document.id,
            document_version_id=version.id,
            original_format=original_format,
            original_filename=filename,
            media_type=media_type,
            size_bytes=1,
            sha256="1" * 64,
            object_key=object_key,
            created_by_id=user_id,
            status="passed" if not with_open_gates else "uploaded",
        )
        check = FormatCheck(
            id=uuid4(),
            external_edit_result_id=result.id,
            automatic_check_completed=not with_open_gates,
            visual_review="passed" if not with_open_gates else "pending",
            unresolved_difference_count=0,
        )
        workflow = ApprovalWorkflow(
            id=uuid4(),
            document_id=document.id,
            status="completed" if not with_open_gates else "pending",
            is_started=True,
        )
        step = ApprovalStep(
            id=uuid4(),
            workflow_id=workflow.id,
            name="Approval",
            assignee_id=user_id,
            sequence=1,
            status="completed" if not with_open_gates else "current",
        )
        session.add_all([document, version, result, check, workflow, step])
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
        return document.id, result.id


async def _resolve_all_gates(document_id: UUID) -> None:
    async with async_session() as session:
        requests = (
            await session.scalars(
                select(ChangeRequest).where(ChangeRequest.document_id == document_id)
            )
        ).all()
        for change_request in requests:
            change_request.status = "accepted"
            proposals = (
                await session.scalars(
                    select(ChangeProposal).where(
                        ChangeProposal.change_request_id == change_request.id
                    )
                )
            ).all()
            for proposal in proposals:
                proposal.status = "accepted"
        relationships = (
            await session.scalars(
                select(DocumentRelationship).where(
                    DocumentRelationship.source_document_id == document_id
                )
            )
        ).all()
        for relationship in relationships:
            relationship.status = "confirmed"
        impacts = (
            await session.scalars(
                select(DocumentImpact).where(DocumentImpact.source_document_id == document_id)
            )
        ).all()
        for impact in impacts:
            impact.status = "confirmed"
        links = (
            await session.scalars(
                select(DocumentEvidenceLink).where(DocumentEvidenceLink.document_id == document_id)
            )
        ).all()
        for link in links:
            link.status = "confirmed"
            link.freshness = "current"
        workflow = await session.scalar(
            select(ApprovalWorkflow).where(ApprovalWorkflow.document_id == document_id)
        )
        assert workflow is not None
        workflow.status = "completed"
        steps = (
            await session.scalars(
                select(ApprovalStep).where(ApprovalStep.workflow_id == workflow.id)
            )
        ).all()
        for step in steps:
            step.status = "completed"
        result = await session.scalar(
            select(ExternalEditResult).where(ExternalEditResult.document_id == document_id)
        )
        assert result is not None
        result.status = "passed"
        check = await session.scalar(
            select(FormatCheck).where(FormatCheck.external_edit_result_id == result.id)
        )
        assert check is not None
        check.automatic_check_completed = True
        check.visual_review = "passed"
        await session.commit()


@pytest.fixture
def completion_client(client: TestClient) -> TestClient:
    storage = MemoryStorage({"private/docx-object": b"docx", "private/pdf-object": b"pdf"})
    app.dependency_overrides[completion_router._storage] = lambda: storage
    try:
        yield client
    finally:
        app.dependency_overrides.pop(completion_router._storage, None)


def test_completion_gates_and_same_format_approval_exports(completion_client: TestClient) -> None:
    email = f"completion-{uuid4()}@example.com"

    async def create_user() -> UUID:
        async with async_session() as session:
            user = User(
                email=email, display_name="Completer", password_hash=hash_password("password")
            )
            session.add(user)
            await session.commit()
            return user.id

    user_id = asyncio.run(create_user())
    assert (
        completion_client.post(
            "/api/v1/auth/login", json={"email": email, "password": "password"}
        ).status_code
        == 200
    )

    docx_document_id, docx_result_id = asyncio.run(
        _create_document(
            user_id=user_id,
            input_kind="editable_docx",
            original_format="docx",
            filename="approved.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            object_key="private/docx-object",
            with_open_gates=True,
        )
    )
    payload = {"document_id": str(docx_document_id), "external_edit_result_id": str(docx_result_id)}
    evaluation = completion_client.post("/api/v1/completion/evaluate", json=payload)
    assert evaluation.status_code == 200
    codes = {reason["code"] for reason in evaluation.json()["blocking_reasons"]}
    assert {
        "format_result_not_passed",
        "automatic_check_incomplete",
        "visual_review_incomplete",
        "pending_change_requests",
        "pending_change_proposals",
        "pending_relationship_candidates",
        "pending_impact_candidates",
        "pending_evidence_candidates",
        "stale_evidence",
        "approval_steps_incomplete",
    } <= codes
    assert completion_client.post("/api/v1/completion", json=payload).status_code == 409
    assert (
        completion_client.get(f"/api/v1/completion/documents/{docx_document_id}/export").status_code
        == 409
    )

    asyncio.run(_resolve_all_gates(docx_document_id))
    completed = completion_client.post("/api/v1/completion", json=payload)
    assert completed.status_code == 201
    assert completion_client.post("/api/v1/completion", json=payload).status_code == 409
    docx_export = completion_client.get(f"/api/v1/completion/documents/{docx_document_id}/export")
    assert docx_export.status_code == 200
    assert docx_export.content == b"docx"
    assert docx_export.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert "approved.docx" in docx_export.headers["content-disposition"]
    assert "private/docx-object" not in str(dict(docx_export.headers))

    pdf_document_id, pdf_result_id = asyncio.run(
        _create_document(
            user_id=user_id,
            input_kind="text_pdf",
            original_format="pdf",
            filename="approved.pdf",
            media_type="application/pdf",
            object_key="private/pdf-object",
        )
    )
    pdf_payload = {
        "document_id": str(pdf_document_id),
        "external_edit_result_id": str(pdf_result_id),
    }
    assert completion_client.post("/api/v1/completion", json=pdf_payload).status_code == 201
    pdf_export = completion_client.get(f"/api/v1/completion/documents/{pdf_document_id}/export")
    assert pdf_export.status_code == 200
    assert pdf_export.content == b"pdf"
    assert pdf_export.headers["content-type"].startswith("application/pdf")
    assert "approved.pdf" in pdf_export.headers["content-disposition"]
    assert "private/pdf-object" not in str(dict(pdf_export.headers))

    scanned_document_id, scanned_result_id = asyncio.run(
        _create_document(
            user_id=user_id,
            input_kind="scanned_pdf",
            original_format="pdf",
            filename="scan.pdf",
            media_type="application/pdf",
            object_key="private/scan-pdf-object",
        )
    )
    scanned_payload = {
        "document_id": str(scanned_document_id),
        "external_edit_result_id": str(scanned_result_id),
    }
    scanned = completion_client.post("/api/v1/completion/evaluate", json=scanned_payload)
    assert {reason["code"] for reason in scanned.json()["blocking_reasons"]} == {"scanned_pdf"}
    assert completion_client.post("/api/v1/completion", json=scanned_payload).status_code == 409
    assert (
        completion_client.get(
            f"/api/v1/completion/documents/{scanned_document_id}/export"
        ).status_code
        == 409
    )

    cross_document_id, cross_result_id = asyncio.run(
        _create_document(
            user_id=user_id,
            input_kind="text_pdf",
            original_format="docx",
            filename="cross.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            object_key="private/cross-docx-object",
        )
    )
    cross_payload = {
        "document_id": str(cross_document_id),
        "external_edit_result_id": str(cross_result_id),
    }
    cross = completion_client.post("/api/v1/completion/evaluate", json=cross_payload)
    assert {reason["code"] for reason in cross.json()["blocking_reasons"]} == {
        "cross_format_result"
    }
    assert completion_client.post("/api/v1/completion", json=cross_payload).status_code == 409
