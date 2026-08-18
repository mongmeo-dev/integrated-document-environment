import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.approvals.models import ApprovalWorkflow, ApprovalWorkflowAudit
from ide_api.domains.auth.models import User
from ide_api.domains.changes.models import ChangeProposal, ChangeRequest
from ide_api.domains.completion.models import DocumentCompletion
from ide_api.domains.documents.models import Document, DocumentVersion
from ide_api.domains.evidence.models import DocumentEvidenceLink, EvidenceItem
from ide_api.domains.formatting.models import ExternalEditResult, FormatCheck
from ide_api.domains.impacts.models import DocumentImpact, DocumentRelationship


async def _create_history_data() -> tuple[UUID, str]:
    now = datetime.now(UTC).replace(microsecond=0)
    async with async_session() as session:
        user = User(
            email=f"history-{now.timestamp()}@neudive.com",
            display_name="History reviewer",
            password_hash=hash_password("correct-horse-battery-staple"),
        )
        document = Document()
        session.add_all([user, document])
        await session.flush()

        version = DocumentVersion(
            document_id=document.id,
            original_filename="history.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=1,
            sha256="0" * 64,
            object_key="private/history.docx",
            created_by_id=user.id,
            status="queued",
        )
        request = ChangeRequest(
            document_id=document.id,
            requester_id=user.id,
            title="Clarify history",
            description="Record the decision reason.",
            created_at=now,
        )
        relationship = DocumentRelationship(
            source_document_id=document.id,
            source_location="1",
            target_document_id=document.id,
            target_location="2",
            relationship_type="references",
            reason="Cross-reference is required.",
            status="confirmed",
            decided_by_id=user.id,
            created_at=now,
            decided_at=now + timedelta(seconds=2),
        )
        impact = DocumentImpact(
            source_document_id=document.id,
            source_location="1",
            target_document_id=document.id,
            target_location="2",
            reason="The target needs revision.",
            proposed_modification="Update target.",
            status="confirmed",
            modification_required=True,
            decided_by_id=user.id,
            modification_decided_by_id=user.id,
            created_at=now,
            decided_at=now + timedelta(seconds=3),
            modification_decided_at=now + timedelta(seconds=4),
        )
        evidence = EvidenceItem(
            evidence_type="description",
            title="History evidence",
            description="Persistent evidence.",
        )
        workflow = ApprovalWorkflow(document_id=document.id, is_started=True, status="in_progress")
        session.add_all([version, request, relationship, impact, evidence, workflow])
        await session.flush()

        proposal = ChangeProposal(
            change_request_id=request.id,
            proposed_text="Use one event schema.",
            rationale="Makes audit review consistent.",
            status="accepted",
            decided_by_id=user.id,
            created_at=now,
            decided_at=now + timedelta(seconds=1),
        )
        evidence_link = DocumentEvidenceLink(
            document_id=document.id,
            evidence_id=evidence.id,
            status="confirmed",
            freshness="stale",
            reason="The source version changed.",
            decided_by_id=user.id,
            reviewed_by_id=user.id,
            created_at=now,
            decided_at=now + timedelta(seconds=5),
            reviewed_at=now + timedelta(seconds=6),
        )
        audit = ApprovalWorkflowAudit(
            workflow_id=workflow.id,
            actor_id=user.id,
            reason="Approved after review.",
            changed_at=now + timedelta(seconds=7),
            before_json={"status": "in_progress"},
            after_json={"status": "approved"},
        )
        result = ExternalEditResult(
            document_id=document.id,
            document_version_id=version.id,
            original_format="docx",
            original_filename="history.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=1,
            sha256="1" * 64,
            object_key="private/external-history.docx",
            status="passed",
            created_by_id=user.id,
            created_at=now,
        )
        session.add_all([proposal, evidence_link, audit, result])
        await session.flush()
        check = FormatCheck(
            external_edit_result_id=result.id,
            automatic_check_completed=True,
            visual_review="passed",
            created_at=now,
            updated_at=now + timedelta(seconds=8),
        )
        completion = DocumentCompletion(
            document_id=document.id,
            external_edit_result_id=result.id,
            original_format="docx",
            completed_by_id=user.id,
            completed_at=now + timedelta(seconds=9),
        )
        session.add_all([check, completion])
        await session.commit()
        return document.id, user.email


def test_history_merges_persistent_domain_events_in_reverse_time_order(client: TestClient) -> None:
    document_id, email = asyncio.run(_create_history_data())

    unauthenticated = client.get(f"/api/v1/history?document_id={document_id}")
    assert unauthenticated.status_code == 401

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert login.status_code == 200

    response = client.get(f"/api/v1/history?document_id={document_id}&limit=50")
    assert response.status_code == 200
    events = response.json()
    assert [event["occurred_at"] for event in events] == sorted(
        (event["occurred_at"] for event in events), reverse=True
    )
    assert {event["type"] for event in events} >= {
        "change_request",
        "change_proposal_decision",
        "document_relationship_decision",
        "document_impact_decision",
        "evidence_decision",
        "evidence_stale",
        "evidence_review",
        "approval_audit",
        "format_check_completed",
        "visual_review",
        "document_completion",
    }
    approval = next(event for event in events if event["type"] == "approval_audit")
    assert approval["actor_id"] is not None
    assert approval["reason"] == "Approved after review."
    assert approval["before"] == {"status": "in_progress"}
    assert approval["after"] == {"status": "approved"}
    assert all("object_key" not in event for event in events)

    filtered = client.get(f"/api/v1/history?document_id={document_id}&filter=approval_audit")
    assert filtered.status_code == 200
    assert [event["type"] for event in filtered.json()] == ["approval_audit"]
