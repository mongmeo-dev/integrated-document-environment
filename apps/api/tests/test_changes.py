import asyncio
from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User
from ide_api.domains.documents.models import Document, DocumentVersion


async def _reset_change_data() -> tuple[UUID, UUID]:
    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))

        user = User(
            email="developer@neudive.com",
            display_name="김민준",
            password_hash=hash_password("correct-horse-battery-staple"),
        )
        document = Document()
        session.add_all([user, document])
        await session.flush()
        document_version = DocumentVersion(
            document_id=document.id,
            original_filename="requirements.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=1,
            sha256="0" * 64,
            object_key="test/requirements.docx",
            created_by_id=user.id,
            status="queued",
        )
        session.add(document_version)
        await session.commit()
        return user.id, document.id


@pytest.fixture
def auth_data() -> Generator[tuple[UUID, UUID]]:
    yield asyncio.run(_reset_change_data())
    asyncio.run(_reset_change_data())


async def _get_document_version_status(document_id: UUID) -> tuple[str, str | None]:
    async with async_session() as session:
        document_version = (
            await session.execute(
                select(DocumentVersion).where(DocumentVersion.document_id == document_id)
            )
        ).scalar_one()
        return document_version.status, document_version.input_kind


def test_change_request_proposal_acceptance_does_not_complete_document(
    client: TestClient,
    auth_data: tuple[UUID, UUID],
) -> None:
    user_id, document_id = auth_data
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "developer@neudive.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert login_response.status_code == 200

    create_response = client.post(
        "/api/v1/changes",
        json={
            "document_id": str(document_id),
            "title": "Clarify retention period",
            "description": "The audit-log retention requirement needs clarification.",
        },
    )
    assert create_response.status_code == 201
    change_request = create_response.json()
    assert change_request["requester_id"] == str(user_id)
    change_request_id = change_request["id"]

    list_response = client.get(f"/api/v1/changes?document_id={document_id}")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [change_request_id]

    transition_response = client.patch(
        f"/api/v1/changes/{change_request_id}/status",
        json={"status": "in_review"},
    )
    assert transition_response.status_code == 200
    assert transition_response.json()["status"] == "in_review"

    proposal_response = client.post(
        f"/api/v1/changes/{change_request_id}/proposals",
        json={
            "proposed_text": "Retain audit logs for seven years.",
            "rationale": "This meets the regulatory retention requirement.",
        },
    )
    assert proposal_response.status_code == 201
    proposal_id = proposal_response.json()["id"]

    decision_response = client.patch(
        f"/api/v1/changes/{change_request_id}/proposals/{proposal_id}/decision",
        json={"status": "accepted"},
    )
    assert decision_response.status_code == 200
    assert decision_response.json()["decided_by_id"] == str(user_id)
    assert decision_response.json()["status"] == "accepted"

    detail_response = client.get(f"/api/v1/changes/{change_request_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["proposals"] == [
        {
            **decision_response.json(),
        }
    ]

    document_version_status, input_kind = asyncio.run(_get_document_version_status(document_id))
    assert document_version_status == "queued"
    assert input_kind is None

    second_decision_response = client.patch(
        f"/api/v1/changes/{change_request_id}/proposals/{proposal_id}/decision",
        json={"status": "accepted"},
    )
    assert second_decision_response.status_code == 409
    assert second_decision_response.json()["detail"]["code"] == (
        "invalid_change_proposal_transition"
    )
