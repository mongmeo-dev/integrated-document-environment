from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.domains.auth.schemas import ApiError
from ide_api.domains.changes.models import ChangeRequest
from ide_api.domains.changes.schemas import (
    ChangeCommentCreate,
    ChangeCommentResponse,
    ChangeCommentStatus,
    ChangeProposalCreate,
    ChangeProposalResponse,
    ChangeProposalStatus,
    ChangeRequestCreate,
    ChangeRequestResponse,
    ChangeRequestStatus,
)
from ide_api.domains.changes.service import (
    ChangeCommentNotFoundError,
    ChangeProposalNotFoundError,
    ChangeRequestNotFoundError,
    ChangeRequestService,
    InvalidChangeProposalTransitionError,
    InvalidChangeRequestTransitionError,
    UnauthorizedChangeCommentTransitionError,
)

router = APIRouter(prefix="/changes", tags=["changes"])


class ChangeRequestTransition(BaseModel):
    status: ChangeRequestStatus


class ChangeProposalDecision(BaseModel):
    status: ChangeProposalStatus


class ChangeCommentTransition(BaseModel):
    status: ChangeCommentStatus


def _change_request_response(change_request: ChangeRequest) -> ChangeRequestResponse:
    return ChangeRequestResponse(
        id=change_request.id,
        document_id=change_request.document_id,
        requester_id=change_request.requester_id,
        title=change_request.title,
        description=change_request.description,
        status=change_request.status,
        assignee_id=change_request.assignee_id,
        created_at=change_request.created_at,
        updated_at=change_request.updated_at,
        proposals=[],
        comments=[],
    )


def _parse_change_request_id(change_request_id: str) -> UUID:
    try:
        return UUID(change_request_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_request_not_found",
                message="Change request not found.",
            ).model_dump(),
        ) from None


def _parse_proposal_id(proposal_id: str) -> UUID:
    try:
        return UUID(proposal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_proposal_not_found",
                message="Change proposal not found.",
            ).model_dump(),
        ) from None


def _parse_comment_id(comment_id: str) -> UUID:
    try:
        return UUID(comment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_comment_not_found",
                message="Change comment not found.",
            ).model_dump(),
        ) from None


@router.post(
    "",
    operation_id="createChangeRequest",
    response_model=ChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}},
)
async def create_change_request(
    data: ChangeRequestCreate,
    response: Response,
    db_session: DbSession,
    current_user: CurrentUser,
) -> ChangeRequestResponse:
    change_request = await ChangeRequestService(db_session).create_change_request(
        requester_id=current_user.id,
        data=data,
    )
    response.headers["Location"] = f"/api/v1/changes/{change_request.id}"
    return _change_request_response(change_request)


@router.get(
    "",
    operation_id="listChangeRequests",
    response_model=list[ChangeRequestResponse],
    responses={401: {"model": ApiError}},
)
async def list_change_requests(
    document_id: Annotated[UUID, Query()],
    db_session: DbSession,
    _: CurrentUser,
) -> list[ChangeRequestResponse]:
    change_requests = await ChangeRequestService(db_session).list_change_requests(
        document_id=document_id
    )
    return [_change_request_response(change_request) for change_request in change_requests]


@router.get(
    "/{change_request_id}",
    operation_id="getChangeRequest",
    response_model=ChangeRequestResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def get_change_request(
    change_request_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> ChangeRequestResponse:
    try:
        return await ChangeRequestService(db_session).get_change_request(
            change_request_id=_parse_change_request_id(change_request_id)
        )
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_request_not_found",
                message="Change request not found.",
            ).model_dump(),
        ) from None


@router.post(
    "/{change_request_id}/proposals",
    operation_id="createChangeProposal",
    response_model=ChangeProposalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def create_change_proposal(
    change_request_id: str,
    data: ChangeProposalCreate,
    response: Response,
    db_session: DbSession,
    _: CurrentUser,
) -> ChangeProposalResponse:
    parsed_change_request_id = _parse_change_request_id(change_request_id)
    try:
        proposal = await ChangeRequestService(db_session).create_proposal(
            change_request_id=parsed_change_request_id,
            data=data,
        )
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_request_not_found",
                message="Change request not found.",
            ).model_dump(),
        ) from None

    response.headers["Location"] = (
        f"/api/v1/changes/{parsed_change_request_id}/proposals/{proposal.id}"
    )
    return ChangeProposalResponse.model_validate(proposal)


@router.post(
    "/{change_request_id}/comments",
    operation_id="createChangeComment",
    response_model=ChangeCommentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def create_change_comment(
    change_request_id: str,
    data: ChangeCommentCreate,
    response: Response,
    db_session: DbSession,
    current_user: CurrentUser,
) -> ChangeCommentResponse:
    parsed_change_request_id = _parse_change_request_id(change_request_id)
    try:
        comment = await ChangeRequestService(db_session).create_comment(
            change_request_id=parsed_change_request_id,
            author_id=current_user.id,
            data=data,
        )
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_request_not_found",
                message="Change request not found.",
            ).model_dump(),
        ) from None

    response.headers["Location"] = (
        f"/api/v1/changes/{parsed_change_request_id}/comments/{comment.id}"
    )
    return ChangeCommentResponse.model_validate(comment)


@router.get(
    "/{change_request_id}/comments",
    operation_id="listChangeComments",
    response_model=list[ChangeCommentResponse],
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def list_change_comments(
    change_request_id: str,
    db_session: DbSession,
    _: CurrentUser,
    assignee_id: Annotated[UUID | None, Query()] = None,
    comment_status: Annotated[ChangeCommentStatus | None, Query(alias="status")] = None,
) -> list[ChangeCommentResponse]:
    try:
        comments = await ChangeRequestService(db_session).list_comments(
            change_request_id=_parse_change_request_id(change_request_id),
            assignee_id=assignee_id,
            status=comment_status,
        )
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_request_not_found",
                message="Change request not found.",
            ).model_dump(),
        ) from None
    return [ChangeCommentResponse.model_validate(comment) for comment in comments]


@router.patch(
    "/{change_request_id}/comments/{comment_id}/status",
    operation_id="transitionChangeComment",
    response_model=ChangeCommentResponse,
    responses={401: {"model": ApiError}, 403: {"model": ApiError}, 404: {"model": ApiError}},
)
async def transition_change_comment(
    change_request_id: str,
    comment_id: str,
    data: ChangeCommentTransition,
    db_session: DbSession,
    current_user: CurrentUser,
) -> ChangeCommentResponse:
    try:
        comment = await ChangeRequestService(db_session).transition_comment(
            change_request_id=_parse_change_request_id(change_request_id),
            comment_id=_parse_comment_id(comment_id),
            status=data.status,
            actor_id=current_user.id,
        )
    except ChangeCommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_comment_not_found",
                message="Change comment not found.",
            ).model_dump(),
        ) from None
    except UnauthorizedChangeCommentTransitionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ApiError(
                code="change_comment_transition_forbidden",
                message="Only the comment author or assignee can change its status.",
            ).model_dump(),
        ) from None

    return ChangeCommentResponse.model_validate(comment)


@router.patch(
    "/{change_request_id}/status",
    operation_id="transitionChangeRequest",
    response_model=ChangeRequestResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def transition_change_request(
    change_request_id: str,
    data: ChangeRequestTransition,
    db_session: DbSession,
    _: CurrentUser,
) -> ChangeRequestResponse:
    try:
        change_request = await ChangeRequestService(db_session).transition_change_request(
            change_request_id=_parse_change_request_id(change_request_id),
            status=data.status,
        )
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_request_not_found",
                message="Change request not found.",
            ).model_dump(),
        ) from None
    except InvalidChangeRequestTransitionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ApiError(
                code="invalid_change_request_transition",
                message="Change request status transition is not allowed.",
            ).model_dump(),
        ) from None

    return _change_request_response(change_request)


@router.patch(
    "/{change_request_id}/proposals/{proposal_id}/decision",
    operation_id="decideChangeProposal",
    response_model=ChangeProposalResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def decide_change_proposal(
    change_request_id: str,
    proposal_id: str,
    data: ChangeProposalDecision,
    db_session: DbSession,
    current_user: CurrentUser,
) -> ChangeProposalResponse:
    try:
        proposal = await ChangeRequestService(db_session).decide_proposal(
            change_request_id=_parse_change_request_id(change_request_id),
            proposal_id=_parse_proposal_id(proposal_id),
            status=data.status,
            decided_by_id=current_user.id,
        )
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_request_not_found",
                message="Change request not found.",
            ).model_dump(),
        ) from None
    except ChangeProposalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code="change_proposal_not_found",
                message="Change proposal not found.",
            ).model_dump(),
        ) from None
    except InvalidChangeProposalTransitionError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ApiError(
                code="invalid_change_proposal_transition",
                message="Change proposal decision is not allowed.",
            ).model_dump(),
        ) from None

    return ChangeProposalResponse.model_validate(proposal)
