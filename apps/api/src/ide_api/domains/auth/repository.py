from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ide_api.domains.auth.models import User, UserSession


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_active_session_by_token_digest(
        self,
        token_digest: str,
        *,
        now: datetime | None = None,
    ) -> UserSession | None:
        current_time = now or datetime.now(UTC)
        result = await self._session.execute(
            select(UserSession)
            .join(UserSession.user)
            .options(selectinload(UserSession.user))
            .where(
                UserSession.token_digest == token_digest,
                UserSession.expires_at > current_time,
                User.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    def add_session(self, user_session: UserSession) -> None:
        self._session.add(user_session)

    async def delete_session(self, user_session: UserSession) -> None:
        await self._session.delete(user_session)
