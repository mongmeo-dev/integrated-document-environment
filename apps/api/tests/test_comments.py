import asyncio
from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User
from ide_api.domains.changes.models import ChangeRequest
from ide_api.domains.documents.models import Document


async def _reset_comment_data() -> tuple[UUID, UUID, UUID, UUID, UUID]:
    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))

        author = User(
            email="comment-author@example.com",
            display_name="Comment Author",
            password_hash=hash_password("author-password"),
        )
        assignee = User(
            email="comment-assignee@example.com",
            display_name="Comment Assignee",
            password_hash=hash_password("assignee-password"),
        )
        outsider = User(
            email="comment-outsider@example.com",
            display_name="Comment Outsider",
            password_hash=hash_password("outsider-password"),
        )
        document = Document()
        session.add_all([author, assignee, outsider, document])
        await session.flush()

        change_request = ChangeRequest(
            document_id=document.id,
            requester_id=author.id,
            assignee_id=assignee.id,
            title="Clarify comment handling",
            description="Reviewers need to resolve assigned comments.",
            status="open",
        )
        session.add(change_request)
        await session.commit()
        return author.id, assignee.id, outsider.id, document.id, change_request.id


@pytest.fixture
def comment_data() -> Generator[tuple[UUID, UUID, UUID, UUID, UUID]]:
    yield asyncio.run(_reset_comment_data())
    asyncio.run(_reset_comment_data())


def _login(client: TestClient, email: str, password: str) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200


def test_comment_assignee_can_resolve_and_reopen_while_outsider_is_forbidden(
    client: TestClient,
    comment_data: tuple[UUID, UUID, UUID, UUID, UUID],
) -> None:
    author_id, assignee_id, _, _, change_request_id = comment_data
    _login(client, "comment-author@example.com", "author-password")

    empty_comment = client.post(
        f"/api/v1/changes/{change_request_id}/comments",
        json={"body": "   ", "assignee_id": str(assignee_id)},
    )
    assert empty_comment.status_code == 422

    create_comment = client.post(
        f"/api/v1/changes/{change_request_id}/comments",
        json={
            "body": "Please cite the applicable retention policy.",
            "assignee_id": str(assignee_id),
        },
    )
    assert create_comment.status_code == 201
    comment = create_comment.json()
    comment_id = comment["id"]
    assert comment["author_id"] == str(author_id)
    assert comment["assignee_id"] == str(assignee_id)
    assert comment["body"] == "Please cite the applicable retention policy."
    assert comment["status"] == "open"
    assert comment["resolved_by_id"] is None
    assert comment["resolved_at"] is None

    _login(client, "comment-outsider@example.com", "outsider-password")
    forbidden_transition = client.patch(
        f"/api/v1/changes/{change_request_id}/comments/{comment_id}/status",
        json={"status": "resolved"},
    )
    assert forbidden_transition.status_code == 403
    assert forbidden_transition.json()["detail"]["code"] == "change_comment_transition_forbidden"

    _login(client, "comment-assignee@example.com", "assignee-password")
    resolved = client.patch(
        f"/api/v1/changes/{change_request_id}/comments/{comment_id}/status",
        json={"status": "resolved"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_by_id"] == str(assignee_id)
    assert resolved.json()["resolved_at"] is not None

    detail = client.get(f"/api/v1/changes/{change_request_id}")
    assert detail.status_code == 200
    assert detail.json()["comments"] == [resolved.json()]

    reopened = client.patch(
        f"/api/v1/changes/{change_request_id}/comments/{comment_id}/status",
        json={"status": "open"},
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "open"
    assert reopened.json()["resolved_by_id"] is None
    assert reopened.json()["resolved_at"] is None
