from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ide_api.config import get_settings
from ide_api.core.database import get_session
from ide_api.domains.auth.models import User
from ide_api.domains.auth.schemas import ApiError
from ide_api.domains.auth.service import AuthService, InvalidSessionError

DbSession = Annotated[AsyncSession, Depends(get_session)]
_settings = get_settings()


async def get_current_user(
    db_session: DbSession,
    session_token: Annotated[
        str | None,
        Cookie(alias=_settings.session_cookie_name),
    ] = None,
) -> User:
    if session_token is None:
        raise HTTPException(
            status_code=401,
            detail=ApiError(
                code="authentication_required",
                message="Authentication required.",
            ).model_dump(),
        )

    try:
        return await AuthService(db_session).get_current_user(session_token)
    except InvalidSessionError:
        raise HTTPException(
            status_code=401,
            detail=ApiError(
                code="authentication_required",
                message="Authentication required.",
            ).model_dump(),
        ) from None


CurrentUser = Annotated[User, Depends(get_current_user)]
