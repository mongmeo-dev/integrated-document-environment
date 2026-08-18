from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, File, Form, HTTPException, Response, UploadFile, status

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.domains.auth.schemas import ApiError
from ide_api.domains.formatting.comparison import StorageFormatComparisonRunner
from ide_api.domains.formatting.schemas import (
    ExternalEditResultResponse,
    FormatCheckResponse,
    FormatDifferenceResponse,
    VisualReviewStatus,
)
from ide_api.domains.formatting.service import (
    DocumentVersionNotFoundError,
    ExternalEditResultNotFoundError,
    ExternalEditResultPersistenceError,
    ExternalEditResultStorageError,
    ExternalEditResultUploadError,
    FormatMismatchError,
    FormattingService,
    InvalidFormatCheckTransitionError,
    UnsupportedExternalEditResultError,
)
from ide_api.infrastructure.object_storage import ObjectStorage

router = APIRouter(prefix="/formatting", tags=["formatting"])


def _parse_id(value: str, *, resource: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise _not_found_error(resource) from None


def _not_found_error(resource: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ApiError(
            code=f"{resource}_not_found",
            message=f"{resource.replace('_', ' ').capitalize()} not found.",
        ).model_dump(),
    )


def _conflict_error(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ApiError(code=code, message=message).model_dump(),
    )


def _service(session: DbSession, storage: ObjectStorage | None = None) -> FormattingService:
    return FormattingService(session, StorageFormatComparisonRunner(), storage)


@router.post(
    "/external-results",
    operation_id="collectExternalEditResult",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ApiError},
        401: {"model": ApiError},
        404: {"model": ApiError},
        409: {"model": ApiError},
        413: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def collect_external_edit_result(
    response: Response,
    db_session: DbSession,
    current_user: CurrentUser,
    document_id: Annotated[UUID, Form()],
    document_version_id: Annotated[UUID, Form()],
    file: Annotated[UploadFile, File()],
) -> dict[str, object]:
    try:
        result = await _service(db_session, ObjectStorage()).collect_uploaded_external_edit_result(
            created_by_id=current_user.id,
            document_id=document_id,
            document_version_id=document_version_id,
            upload=file,
        )
    except DocumentVersionNotFoundError:
        raise _not_found_error("document_version") from None
    except FormatMismatchError, UnsupportedExternalEditResultError:
        raise _conflict_error(
            "invalid_external_edit_result", "External result does not match its source."
        ) from None
    except ExternalEditResultUploadError as error:
        status_code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if error.code == "file_too_large"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail=ApiError(code=error.code, message=error.message).model_dump(),
        ) from None
    except ExternalEditResultStorageError, ExternalEditResultPersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ApiError(
                code="external_edit_result_unavailable",
                message="External edit result collection is temporarily unavailable.",
            ).model_dump(),
        ) from None
    response.headers["Location"] = f"/api/v1/formatting/external-results/{result.id}"
    return ExternalEditResultResponse.model_validate(result).model_dump(
        mode="json", exclude={"object_key"}
    )


@router.get(
    "/documents/{document_id}/external-results",
    operation_id="listExternalEditResults",
    response_model=list[ExternalEditResultResponse],
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def list_external_edit_results(
    document_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> list[ExternalEditResultResponse]:
    results = await _service(db_session).list_external_edit_results(
        document_id=_parse_id(document_id, resource="document")
    )
    return [ExternalEditResultResponse.model_validate(result) for result in results]


@router.get(
    "/external-results/{external_edit_result_id}",
    operation_id="getExternalEditResult",
    response_model=ExternalEditResultResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def get_external_edit_result(
    external_edit_result_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> ExternalEditResultResponse:
    try:
        return await _service(db_session).get_external_edit_result(
            external_edit_result_id=_parse_id(
                external_edit_result_id, resource="external_edit_result"
            )
        )
    except ExternalEditResultNotFoundError:
        raise _not_found_error("external_edit_result") from None


@router.post(
    "/external-results/{external_edit_result_id}/automatic-check",
    operation_id="runExternalResultAutomaticFormatCheck",
    response_model=FormatCheckResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def run_automatic_check(
    external_edit_result_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> FormatCheckResponse:
    try:
        check = await _service(db_session).run_automatic_check(
            external_edit_result_id=_parse_id(
                external_edit_result_id, resource="external_edit_result"
            )
        )
    except ExternalEditResultNotFoundError:
        raise _not_found_error("external_edit_result") from None
    except InvalidFormatCheckTransitionError:
        raise _conflict_error(
            "invalid_format_check_transition", "Automatic check is not allowed."
        ) from None
    return FormatCheckResponse.model_validate(check)


@router.get(
    "/external-results/{external_edit_result_id}/format-check",
    operation_id="getExternalResultFormatCheck",
    response_model=FormatCheckResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def get_format_check(
    external_edit_result_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> FormatCheckResponse:
    try:
        return await _service(db_session).get_format_check(
            external_edit_result_id=_parse_id(
                external_edit_result_id, resource="external_edit_result"
            )
        )
    except ExternalEditResultNotFoundError:
        raise _not_found_error("external_edit_result") from None


@router.patch(
    "/external-results/{external_edit_result_id}/visual-review",
    operation_id="completeExternalResultVisualReview",
    response_model=FormatCheckResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def complete_visual_review(
    external_edit_result_id: str,
    db_session: DbSession,
    _: CurrentUser,
    visual_review: Annotated[VisualReviewStatus, Body(embed=True)],
) -> FormatCheckResponse:
    try:
        check = await _service(db_session).complete_visual_review(
            external_edit_result_id=_parse_id(
                external_edit_result_id, resource="external_edit_result"
            ),
            visual_review=visual_review,
        )
    except ExternalEditResultNotFoundError:
        raise _not_found_error("external_edit_result") from None
    except InvalidFormatCheckTransitionError:
        raise _conflict_error(
            "invalid_format_check_transition", "Visual review is not allowed."
        ) from None
    return FormatCheckResponse.model_validate(check)


@router.post(
    "/differences/{difference_id}/resolve",
    operation_id="resolveExternalResultFormatDifference",
    response_model=FormatDifferenceResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def resolve_difference(
    difference_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> FormatDifferenceResponse:
    try:
        difference = await _service(db_session).resolve_difference(
            difference_id=_parse_id(difference_id, resource="format_difference")
        )
    except ExternalEditResultNotFoundError:
        raise _not_found_error("format_difference") from None
    except InvalidFormatCheckTransitionError:
        raise _conflict_error(
            "invalid_format_check_transition", "Difference cannot be resolved now."
        ) from None
    return FormatDifferenceResponse.model_validate(difference)


@router.get(
    "/external-results/{external_edit_result_id}/approval-allowed",
    operation_id="getExternalResultApprovalAllowed",
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def get_approval_allowed(
    external_edit_result_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> dict[str, bool]:
    try:
        allowed = await _service(db_session).is_approval_allowed(
            external_edit_result_id=_parse_id(
                external_edit_result_id, resource="external_edit_result"
            )
        )
    except ExternalEditResultNotFoundError:
        raise _not_found_error("external_edit_result") from None
    return {"allowed": allowed}
