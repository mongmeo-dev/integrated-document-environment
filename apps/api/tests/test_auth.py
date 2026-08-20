import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from ide_api.core.database import async_session
from ide_api.core.security import hash_password
from ide_api.domains.auth.models import User


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
