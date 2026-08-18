import asyncio
from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User, UserSession
from ide_api.domains.documents.models import Document
from ide_api.domains.evidence.models import DocumentEvidenceLink, EvidenceItem


async def _reset_evidence_data() -> tuple[UUID, UUID]:
    async with async_session() as session:
        await session.execute(delete(DocumentEvidenceLink))
        await session.execute(delete(EvidenceItem))
        await session.execute(delete(Document))
        await session.execute(delete(UserSession))
        await session.execute(delete(User))

        user = User(
            email="evidence-reviewer@neudive.com",
            display_name="근거 검토자",
            password_hash=hash_password("correct-horse-battery-staple"),
        )
        document = Document()
        session.add_all([user, document])
        await session.commit()
        return user.id, document.id


@pytest.fixture
def auth_data() -> Generator[tuple[UUID, UUID]]:
    yield asyncio.run(_reset_evidence_data())
    asyncio.run(_reset_evidence_data())


def test_document_evidence_candidate_freshness_review_can_be_reopened(
    client: TestClient,
    auth_data: tuple[UUID, UUID],
) -> None:
    user_id, document_id = auth_data

    unauthenticated_response = client.post(
        "/api/v1/evidence/items",
        json={
            "evidence_type": "test_result",
            "title": "API regression result",
            "description": "The API regression suite passed.",
        },
    )
    assert unauthenticated_response.status_code == 401

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "evidence-reviewer@neudive.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert login_response.status_code == 200

    evidence_response = client.post(
        "/api/v1/evidence/items",
        json={
            "evidence_type": "test_result",
            "title": "API regression result",
            "description": "The API regression suite passed.",
            "reference": "run-20260818-001",
        },
    )
    assert evidence_response.status_code == 201
    evidence = evidence_response.json()

    candidate_response = client.post(
        "/api/v1/evidence/links",
        json={
            "document_id": str(document_id),
            "evidence_id": evidence["id"],
            "reason": "This run verifies the document's described API behavior.",
        },
    )
    assert candidate_response.status_code == 201
    candidate = candidate_response.json()
    assert candidate["status"] == "candidate"
    assert candidate["decided_by_id"] is None

    list_response = client.get(f"/api/v1/evidence/documents/{document_id}/links")
    assert list_response.status_code == 200
    assert list_response.json() == [candidate]

    confirmed_response = client.patch(f"/api/v1/evidence/links/{candidate['id']}/confirm")
    assert confirmed_response.status_code == 200
    confirmed = confirmed_response.json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["decided_by_id"] == str(user_id)
    assert confirmed["decided_at"] is not None

    repeat_confirmation_response = client.patch(f"/api/v1/evidence/links/{candidate['id']}/confirm")
    assert repeat_confirmation_response.status_code == 409
    assert (
        repeat_confirmation_response.json()["detail"]["code"]
        == "invalid_document_evidence_link_transition"
    )

    stale_response = client.patch(f"/api/v1/evidence/items/{evidence['id']}/links/stale")
    assert stale_response.status_code == 204

    stale_link_response = client.get(f"/api/v1/evidence/documents/{document_id}/links")
    assert stale_link_response.status_code == 200
    assert stale_link_response.json()[0]["freshness"] == "stale"

    review_response = client.patch(f"/api/v1/evidence/links/{candidate['id']}/freshness-review")
    assert review_response.status_code == 200
    reviewed = review_response.json()
    assert reviewed["freshness"] == "current"
    assert reviewed["reviewed_by_id"] == str(user_id)
    assert reviewed["reviewed_at"] is not None

    reopened_response = client.patch(f"/api/v1/evidence/documents/{document_id}/links/stale")
    assert reopened_response.status_code == 204

    reopened_link_response = client.get(f"/api/v1/evidence/documents/{document_id}/links")
    assert reopened_link_response.status_code == 200
    reopened = reopened_link_response.json()[0]
    assert reopened["freshness"] == "stale"
    assert reopened["reviewed_by_id"] == str(user_id)

    missing_response = client.patch(
        "/api/v1/evidence/links/00000000-0000-0000-0000-000000000000/confirm"
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"]["code"] == "document_evidence_link_not_found"
