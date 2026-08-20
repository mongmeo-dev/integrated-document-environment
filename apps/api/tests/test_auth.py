import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from ide_api.cmd.create_user import create_user
from ide_api.core.database import async_session
from ide_api.core.security import hash_password, verify_password
from ide_api.domains.auth.models import User
from ide_api.domains.auth.repository import AuthRepository


async def _reset_auth_data() -> None:
    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        session.add(
            User(
                email="developer@neudive.com",
                display_name="김민준",
                password_hash=hash_password("correct-horse-battery-staple"),
            )
        )
        await session.commit()


@pytest.fixture(autouse=True)
def auth_data() -> None:
    asyncio.run(_reset_auth_data())


def test_login_me_logout_round_trip(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": " Developer@Neudive.com ",
            "password": "correct-horse-battery-staple",
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["email"] == "developer@neudive.com"
    assert "ide_session=" in login_response.headers["set-cookie"]
    assert "HttpOnly" in login_response.headers["set-cookie"]
    assert "Secure" in login_response.headers["set-cookie"]

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["display_name"] == "김민준"

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    unauthenticated_response = client.get("/api/v1/auth/me")
    assert unauthenticated_response.status_code == 401
    assert unauthenticated_response.json()["detail"]["code"] == "authentication_required"


def test_login_does_not_reveal_account_existence(client: TestClient) -> None:
    unknown_response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@neudive.com", "password": "wrong"},
    )
    wrong_password_response = client.post(
        "/api/v1/auth/login",
        json={"email": "developer@neudive.com", "password": "wrong"},
    )

    assert unknown_response.status_code == 401
    assert wrong_password_response.status_code == 401
    assert unknown_response.json() == wrong_password_response.json()
    assert unknown_response.json()["detail"]["code"] == "invalid_credentials"


def test_create_user_command_creates_login_account() -> None:
    user = asyncio.run(
        create_user(
            email=" New.User@Neudive.com ",
            display_name=" 새 사용자 ",
            password="new-user-password",
        )
    )

    async def load_user() -> User | None:
        async with async_session() as session:
            return await AuthRepository(session).get_user_by_email("new.user@neudive.com")

    saved_user = asyncio.run(load_user())

    assert user.email == "new.user@neudive.com"
    assert user.display_name == "새 사용자"
    assert saved_user is not None
    assert verify_password("new-user-password", saved_user.password_hash)


def test_create_user_command_rejects_duplicate_email() -> None:
    with pytest.raises(ValueError, match="already exists"):
        asyncio.run(
            create_user(
                email=" Developer@Neudive.com ",
                display_name="중복 사용자",
                password="duplicate-password",
            )
        )
