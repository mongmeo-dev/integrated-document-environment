from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.config import get_settings
from ide_api.core.security import (
    digest_session_token,
    generate_session_token,
    verify_password,
)
from ide_api.domains.auth.models import User, UserSession
from ide_api.domains.auth.repository import AuthRepository


class InvalidCredentialsError(Exception):
    pass


class InvalidSessionError(Exception):
    pass


class LoginResult:
    def __init__(self, user: User, token: str) -> None:
        self.user = user
        self.token = token


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = AuthRepository(session)

    async def login(self, *, email: str, password: str) -> LoginResult:
        user = await self._repository.get_user_by_email(email.strip().lower())
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError

        token = generate_session_token()
        expires_at = datetime.now(UTC) + timedelta(seconds=get_settings().session_ttl_seconds)
        self._repository.add_session(
            UserSession(
                user_id=user.id,
                token_digest=digest_session_token(token),
                expires_at=expires_at,
            )
        )
        await self._session.commit()
        return LoginResult(user=user, token=token)

    async def get_current_user(self, token: str) -> User:
        user_session = await self._repository.get_active_session_by_token_digest(
            digest_session_token(token)
        )
        if user_session is None:
            raise InvalidSessionError
        return user_session.user

    async def logout(self, token: str) -> None:
        user_session = await self._repository.get_active_session_by_token_digest(
            digest_session_token(token)
        )
        if user_session is None:
            raise InvalidSessionError

        await self._repository.delete_session(user_session)
        await self._session.commit()
