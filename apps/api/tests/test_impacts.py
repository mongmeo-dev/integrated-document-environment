import asyncio
from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User
from ide_api.domains.documents.models import Document


async def _reset_impact_data() -> tuple[UUID, UUID]:
    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))

        user = User(
            email="developer@neudive.com",
            display_name="김민준",
            password_hash=hash_password("correct-horse-battery-staple"),
        )
        document = Document()
        session.add_all([user, document])
        await session.commit()
        return user.id, document.id


@pytest.fixture
def auth_data() -> Generator[tuple[UUID, UUID]]:
    yield asyncio.run(_reset_impact_data())
    asyncio.run(_reset_impact_data())


def test_impact_candidate_confirmation_and_modification_decision(
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

    relationship_response = client.post(
        "/api/v1/impacts/relationships",
        json={
            "source_document_id": str(document_id),
            "source_location": "section:scope",
            "target_document_id": str(document_id),
            "target_location": "section:requirements",
            "relationship_type": "semantic",
            "reason": "The requirements refine the stated scope.",
        },
    )
    assert relationship_response.status_code == 201
    relationship = relationship_response.json()
    assert relationship["status"] == "candidate"
    assert relationship["decided_by_id"] is None

    impact_response = client.post(
        "/api/v1/impacts/candidates",
        json={
            "source_document_id": str(document_id),
            "source_location": "paragraph:12",
            "target_document_id": str(document_id),
            "target_location": "table:3,row:2",
            "reason": "The changed retention period affects the policy matrix.",
            "proposed_modification": "Update the retention period to seven years.",
        },
    )
    assert impact_response.status_code == 201
    impact = impact_response.json()
    assert impact["status"] == "candidate"
    assert impact["modification_required"] is None

    list_response = client.get(f"/api/v1/impacts/documents/{document_id}")
    assert list_response.status_code == 200
    assert list_response.json() == {
        "document_id": str(document_id),
        "relationships": [relationship],
        "impacts": [impact],
    }
    assert list_response.json()["impacts"][0]["source_location"] == "paragraph:12"
    assert "retention period" in list_response.json()["impacts"][0]["reason"]

    relationship_decision_response = client.patch(
        f"/api/v1/impacts/relationships/{relationship['id']}/confirm"
    )
    assert relationship_decision_response.status_code == 200
    assert relationship_decision_response.json()["status"] == "confirmed"
    assert relationship_decision_response.json()["decided_by_id"] == str(user_id)

    confirmation_response = client.patch(f"/api/v1/impacts/candidates/{impact['id']}/confirm")
    assert confirmation_response.status_code == 200
    assert confirmation_response.json()["status"] == "confirmed"
    assert confirmation_response.json()["decided_by_id"] == str(user_id)

    modification_response = client.patch(
        f"/api/v1/impacts/candidates/{impact['id']}/modification-required"
    )
    assert modification_response.status_code == 200
    assert modification_response.json()["modification_required"] is True
    assert modification_response.json()["modification_decided_by_id"] == str(user_id)

    repeat_decision_response = client.patch(
        f"/api/v1/impacts/candidates/{impact['id']}/modification-not-required"
    )
    assert repeat_decision_response.status_code == 409
    assert repeat_decision_response.json()["detail"]["code"] == "invalid_modification_decision"

    missing_response = client.patch(
        "/api/v1/impacts/candidates/00000000-0000-0000-0000-000000000000/confirm"
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"]["code"] == "impact_candidate_not_found"
