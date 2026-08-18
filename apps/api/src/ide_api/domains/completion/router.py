from typing import Annotated, BinaryIO
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.domains.auth.schemas import ApiError
from ide_api.domains.completion.repository import CompletionRepository
from ide_api.domains.completion.schemas import (
    CompletionEvaluation,
    DocumentCompletionResponse,
)
from ide_api.domains.completion.service import (
    CompletionAlreadyExistsError,
    CompletionBlockedError,
    CompletionService,
)
from ide_api.infrastructure.object_storage import ObjectStorage

router = APIRouter(prefix="/completion", tags=["completion"])


class CompletionRequest(BaseModel):
    document_id: UUID
    external_edit_result_id: UUID


def _service(session: DbSession) -> CompletionService:
    return CompletionService(session)


def _storage() -> ObjectStorage:
    return ObjectStorage()


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


def _attachment_filename(filename: str) -> str:
    safe_filename = filename.replace("\r", "").replace("\n", "").replace('"', "")
    return f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{quote(safe_filename)}"


@router.post(
    "/evaluate",
    operation_id="evaluateDocumentCompletion",
    response_model=CompletionEvaluation,
    responses={401: {"model": ApiError}},
)
async def evaluate_completion(
    request: CompletionRequest,
    db_session: DbSession,
    _: CurrentUser,
) -> CompletionEvaluation:
    return await _service(db_session).evaluate(
        document_id=request.document_id,
        external_edit_result_id=request.external_edit_result_id,
    )


@router.post(
    "",
    operation_id="completeDocument",
    response_model=DocumentCompletionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}, 409: {"model": ApiError}},
)
async def complete_document(
    request: CompletionRequest,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentCompletionResponse:
    try:
        completion = await _service(db_session).complete(
            document_id=request.document_id,
            external_edit_result_id=request.external_edit_result_id,
            completed_by_id=current_user.id,
        )
    except CompletionBlockedError as error:
        raise _conflict_error(
            "document_completion_blocked",
            "Document completion is blocked by outstanding gates.",
        ) from error
    except CompletionAlreadyExistsError:
        raise _conflict_error(
            "document_already_completed", "Document is already completed."
        ) from None
    return DocumentCompletionResponse.model_validate(completion)


@router.get(
    "/documents/{document_id}/export",
    operation_id="downloadApprovalExport",
    responses={
        401: {"model": ApiError},
        404: {"model": ApiError},
        409: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def download_approval_export(
    document_id: UUID,
    db_session: DbSession,
    _: CurrentUser,
    storage: Annotated[ObjectStorage, Depends(_storage)],
) -> StreamingResponse:
    repository = CompletionRepository(db_session)
    if not await repository.document_exists(document_id):
        raise _not_found_error("document")
    completion = await repository.get_completion(document_id)
    if completion is None:
        raise _conflict_error(
            "document_not_completed", "Document must be completed before approval export."
        )
    result_data = await repository.get_external_result(completion.external_edit_result_id)
    if result_data is None:
        raise _not_found_error("external_edit_result")
    result, _, _ = result_data

    evaluation = await _service(db_session).evaluate(
        document_id=document_id,
        external_edit_result_id=completion.external_edit_result_id,
    )
    blocking_reasons = [
        reason
        for reason in evaluation.blocking_reasons
        if reason.code.value != "document_already_completed"
    ]
    if blocking_reasons:
        raise _conflict_error(
            "approval_export_blocked", "Approval export is blocked by outstanding gates."
        )

    try:
        content: BinaryIO = storage.download(result.object_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ApiError(
                code="approval_export_unavailable",
                message="Approval export is temporarily unavailable.",
            ).model_dump(),
        ) from None
    return StreamingResponse(
        content,
        media_type=result.media_type,
        headers={"Content-Disposition": _attachment_filename(result.original_filename)},
    )
