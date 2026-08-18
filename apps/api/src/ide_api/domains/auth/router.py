from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Response, status

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.config import get_settings
from ide_api.domains.auth.models import User
from ide_api.domains.auth.schemas import ApiError, LoginRequest, UserResponse
from ide_api.domains.auth.service import AuthService, InvalidCredentialsError, InvalidSessionError

router = APIRouter(tags=["auth"])
_settings = get_settings()
_SessionToken = Annotated[
    str | None,
    Cookie(alias=_settings.session_cookie_name),
]


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
    )


@router.post(
    "/auth/login",
    operation_id="login",
    response_model=UserResponse,
    responses={401: {"model": ApiError}},
)
async def login(
    request: LoginRequest,
    response: Response,
    db_session: DbSession,
) -> UserResponse:
    try:
        login_result = await AuthService(db_session).login(
            email=request.email,
            password=request.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ApiError(
                code="invalid_credentials",
                message="Invalid email or password.",
            ).model_dump(),
        ) from None

    response.set_cookie(
        key=_settings.session_cookie_name,
        value=login_result.token,
        max_age=_settings.session_ttl_seconds,
        httponly=True,
        secure=_settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return _user_response(login_result.user)


@router.get(
    "/auth/me",
    operation_id="getCurrentUser",
    response_model=UserResponse,
    responses={401: {"model": ApiError}},
)
async def get_current_user(current_user: CurrentUser) -> UserResponse:
    return _user_response(current_user)


@router.post(
    "/auth/logout",
    operation_id="logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ApiError}},
)
async def logout(
    response: Response,
    db_session: DbSession,
    _: CurrentUser,
    session_token: _SessionToken = None,
) -> None:
    if session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ApiError(
                code="authentication_required",
                message="Authentication required.",
            ).model_dump(),
        )

    try:
        await AuthService(db_session).logout(session_token)
    except InvalidSessionError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ApiError(
                code="authentication_required",
                message="Authentication required.",
            ).model_dump(),
        ) from None

    response.delete_cookie(
        key=_settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=_settings.session_cookie_secure,
        samesite="lax",
    )
