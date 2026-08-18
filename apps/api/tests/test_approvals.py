import asyncio
from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.approvals.models import ApprovalStep, ApprovalWorkflow, ApprovalWorkflowAudit
from ide_api.domains.auth.models import User, UserSession
from ide_api.domains.documents.models import Document

PASSWORD = "correct-horse-battery-staple"


async def _reset_approval_data() -> tuple[UUID, UUID, UUID, UUID]:
    async with async_session() as session:
        await session.execute(delete(ApprovalWorkflowAudit))
        await session.execute(delete(ApprovalStep))
        await session.execute(delete(ApprovalWorkflow))
        await session.execute(delete(Document))
        await session.execute(delete(UserSession))
        await session.execute(delete(User))

        first_approver = User(
            email="first-approver@neudive.com",
            display_name="First approver",
            password_hash=hash_password(PASSWORD),
        )
        second_approver = User(
            email="second-approver@neudive.com",
            display_name="Second approver",
            password_hash=hash_password(PASSWORD),
        )
        other_user = User(
            email="other-user@neudive.com",
            display_name="Other user",
            password_hash=hash_password(PASSWORD),
        )
        document = Document()
        session.add_all([first_approver, second_approver, other_user, document])
        await session.commit()
        return first_approver.id, second_approver.id, other_user.id, document.id


@pytest.fixture
def approval_data() -> Generator[tuple[UUID, UUID, UUID, UUID]]:
    yield asyncio.run(_reset_approval_data())
    asyncio.run(_reset_approval_data())


def _login(client: TestClient, email: str) -> None:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200


def test_approval_workflow_enforces_sequential_assignees_and_audits_edits(
    client: TestClient,
    approval_data: tuple[UUID, UUID, UUID, UUID],
) -> None:
    first_approver_id, second_approver_id, _other_user_id, document_id = approval_data
    assert client.post("/api/v1/approvals", json={}).status_code == 401

    _login(client, "first-approver@neudive.com")
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "document_id": str(document_id),
            "steps": [
                {
                    "name": "Legal review",
                    "assignee_id": str(first_approver_id),
                    "sequence": 10,
                },
                {
                    "name": "Security review",
                    "assignee_id": str(second_approver_id),
                    "sequence": 20,
                },
            ],
        },
    )
    assert create_response.status_code == 201
    workflow = create_response.json()
    workflow_id = workflow["id"]
    first_step, second_step = workflow["steps"]

    assert client.get(f"/api/v1/approvals/{workflow_id}").json() == workflow
    assert client.get(f"/api/v1/approvals/documents/{document_id}").json() == workflow
    start_response = client.post(f"/api/v1/approvals/{workflow_id}/start")
    assert start_response.status_code == 200
    assert start_response.json()["steps"][0]["status"] == "current"

    edit_response = client.patch(
        f"/api/v1/approvals/steps/{second_step['id']}",
        json={"name": "Security and privacy review", "reason": "Expanded review scope."},
    )
    assert edit_response.status_code == 200

    missing_reason_response = client.patch(
        f"/api/v1/approvals/steps/{second_step['id']}",
        json={"name": "Security review"},
    )
    assert missing_reason_response.status_code == 409
    assert (
        missing_reason_response.json()["detail"]["code"] == "approval_step_update_reason_required"
    )

    audits_response = client.get(f"/api/v1/approvals/{workflow_id}/audits")
    assert audits_response.status_code == 200
    audit = audits_response.json()[0]
    assert audit["actor_id"] == str(first_approver_id)
    assert audit["reason"] == "Expanded review scope."
    assert audit["before_json"]["steps"][1]["name"] == "Security review"
    assert audit["after_json"]["steps"][1]["name"] == "Security and privacy review"

    _login(client, "other-user@neudive.com")
    unauthorized_response = client.post(f"/api/v1/approvals/steps/{first_step['id']}/approve")
    assert unauthorized_response.status_code == 403
    assert unauthorized_response.json()["detail"]["code"] == "approval_not_authorized"

    skipped_response = client.post(f"/api/v1/approvals/steps/{second_step['id']}/approve")
    assert skipped_response.status_code == 409
    assert skipped_response.json()["detail"]["code"] == "invalid_approval_step_transition"

    _login(client, "first-approver@neudive.com")
    first_approval_response = client.post(f"/api/v1/approvals/steps/{first_step['id']}/approve")
    assert first_approval_response.status_code == 200
    after_first_approval = first_approval_response.json()
    assert after_first_approval["status"] == "current"
    assert after_first_approval["completed_at"] is None
    assert after_first_approval["steps"][0]["status"] == "completed"
    assert after_first_approval["steps"][1]["status"] == "current"

    completed_step_edit_response = client.patch(
        f"/api/v1/approvals/steps/{first_step['id']}",
        json={"name": "Reopened legal review", "reason": "Attempt to change a completed step."},
    )
    assert completed_step_edit_response.status_code == 409
    assert completed_step_edit_response.json()["detail"]["code"] == "approval_step_immutable"

    _login(client, "second-approver@neudive.com")
    final_approval_response = client.post(f"/api/v1/approvals/steps/{second_step['id']}/approve")
    assert final_approval_response.status_code == 200
    assert final_approval_response.json()["status"] == "completed"
    assert final_approval_response.json()["completed_at"] is not None
