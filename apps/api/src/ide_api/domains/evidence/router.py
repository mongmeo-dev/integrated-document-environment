from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.domains.auth.schemas import ApiError
from ide_api.domains.evidence.schemas import (
    DocumentEvidenceLinkCreate,
    DocumentEvidenceLinkResponse,
    EvidenceItemCreate,
    EvidenceItemResponse,
    EvidenceItemUpdate,
)
from ide_api.domains.evidence.service import (
    DocumentEvidenceLinkNotFoundError,
    EvidenceFileEmptyError,
    EvidenceFileNotAvailableError,
    EvidenceFileTooLargeError,
    EvidenceItemNotFoundError,
    EvidenceService,
    InvalidEvidenceLinkTransitionError,
    InvalidFreshnessReviewError,
)

router = APIRouter(prefix="/evidence", tags=["evidence"])


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


def _unprocessable_error(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=ApiError(code=code, message=message).model_dump(),
    )


@router.post(
    "/files",
    operation_id="createEvidenceFile",
    response_model=EvidenceItemResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}, 422: {"model": ApiError}},
)
async def create_evidence_file(
    response: Response,
    db_session: DbSession,
    _: CurrentUser,
    title: Annotated[str, Form(min_length=1, max_length=255)],
    description: Annotated[str, Form(min_length=1)],
    file: Annotated[UploadFile, File()],
    version: Annotated[str | None, Form(max_length=255)] = None,
) -> EvidenceItemResponse:
    try:
        evidence = await EvidenceService(db_session).create_uploaded_evidence_item(
            title=title,
            description=description,
            version=version,
            file=file,
        )
    except EvidenceFileEmptyError:
        raise _unprocessable_error(
            "invalid_evidence_file", "Evidence file must not be empty."
        ) from None
    except EvidenceFileTooLargeError:
        raise _unprocessable_error(
            "evidence_file_too_large", "Evidence file exceeds the upload limit."
        ) from None
    response.headers["Location"] = f"/api/v1/evidence/items/{evidence.id}"
    return EvidenceItemResponse.model_validate(evidence)


@router.get(
    "/{evidence_id}/file",
    operation_id="downloadEvidenceFile",
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def download_evidence_file(
    evidence_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> StreamingResponse:
    try:
        evidence, content = await EvidenceService(db_session).download_evidence_file(
            evidence_id=_parse_id(evidence_id, resource="evidence_item")
        )
    except EvidenceItemNotFoundError, EvidenceFileNotAvailableError:
        raise _not_found_error("evidence_file") from None

    filename = evidence.original_filename or "evidence"
    content_disposition = f"attachment; filename*=UTF-8''{quote(filename, safe='')}"
    return StreamingResponse(
        content,
        media_type=evidence.media_type or "application/octet-stream",
        headers={"Content-Disposition": content_disposition},
    )


@router.post(
    "/items",
    operation_id="createEvidenceItem",
    response_model=EvidenceItemResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}},
)
async def create_evidence_item(
    data: EvidenceItemCreate,
    response: Response,
    db_session: DbSession,
    _: CurrentUser,
) -> EvidenceItemResponse:
    evidence = await EvidenceService(db_session).create_evidence_item(data=data)
    response.headers["Location"] = f"/api/v1/evidence/items/{evidence.id}"
    return EvidenceItemResponse.model_validate(evidence)


@router.get(
    "/items",
    operation_id="listEvidenceItems",
    response_model=list[EvidenceItemResponse],
    responses={401: {"model": ApiError}},
)
async def list_evidence_items(
    db_session: DbSession,
    _: CurrentUser,
) -> list[EvidenceItemResponse]:
    evidence_items = await EvidenceService(db_session).list_evidence_items()
    return [EvidenceItemResponse.model_validate(evidence) for evidence in evidence_items]


@router.get(
    "/items/{evidence_id}",
    operation_id="getEvidenceItem",
    response_model=EvidenceItemResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def get_evidence_item(
    evidence_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> EvidenceItemResponse:
    try:
        evidence = await EvidenceService(db_session).get_evidence_item(
            evidence_id=_parse_id(evidence_id, resource="evidence_item")
        )
    except EvidenceItemNotFoundError:
        raise _not_found_error("evidence_item") from None
    return EvidenceItemResponse.model_validate(evidence)


@router.patch(
    "/items/{evidence_id}",
    operation_id="updateEvidenceItem",
    response_model=EvidenceItemResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def update_evidence_item(
    evidence_id: str,
    data: EvidenceItemUpdate,
    db_session: DbSession,
    _: CurrentUser,
) -> EvidenceItemResponse:
    try:
        evidence = await EvidenceService(db_session).update_evidence_item(
            evidence_id=_parse_id(evidence_id, resource="evidence_item"), data=data
        )
    except EvidenceItemNotFoundError:
        raise _not_found_error("evidence_item") from None
    return EvidenceItemResponse.model_validate(evidence)


@router.post(
    "/links",
    operation_id="createDocumentEvidenceLinkCandidate",
    response_model=DocumentEvidenceLinkResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}},
)
async def create_document_evidence_link_candidate(
    data: DocumentEvidenceLinkCreate,
    response: Response,
    db_session: DbSession,
    _: CurrentUser,
) -> DocumentEvidenceLinkResponse:
    link = await EvidenceService(db_session).create_document_evidence_link(data=data)
    response.headers["Location"] = f"/api/v1/evidence/links/{link.id}"
    return DocumentEvidenceLinkResponse.model_validate(link)


@router.get(
    "/documents/{document_id}/links",
    operation_id="listDocumentEvidenceLinkCandidates",
    response_model=list[DocumentEvidenceLinkResponse],
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def list_document_evidence_link_candidates(
    document_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> list[DocumentEvidenceLinkResponse]:
    links = await EvidenceService(db_session).list_document_evidence_links(
        document_id=_parse_id(document_id, resource="document")
    )
    return [DocumentEvidenceLinkResponse.model_validate(link) for link in links]


@router.patch(
    "/links/{link_id}/confirm",
    operation_id="confirmDocumentEvidenceLinkCandidate",
    response_model=DocumentEvidenceLinkResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def confirm_document_evidence_link_candidate(
    link_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentEvidenceLinkResponse:
    try:
        link = await EvidenceService(db_session).confirm_document_evidence_link(
            link_id=_parse_id(link_id, resource="document_evidence_link"),
            decided_by_id=current_user.id,
        )
    except DocumentEvidenceLinkNotFoundError:
        raise _not_found_error("document_evidence_link") from None
    except InvalidEvidenceLinkTransitionError:
        raise _conflict_error(
            "invalid_document_evidence_link_transition",
            "Document evidence link decision is not allowed.",
        ) from None
    return DocumentEvidenceLinkResponse.model_validate(link)


@router.patch(
    "/links/{link_id}/reject",
    operation_id="rejectDocumentEvidenceLinkCandidate",
    response_model=DocumentEvidenceLinkResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def reject_document_evidence_link_candidate(
    link_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentEvidenceLinkResponse:
    try:
        link = await EvidenceService(db_session).reject_document_evidence_link(
            link_id=_parse_id(link_id, resource="document_evidence_link"),
            decided_by_id=current_user.id,
        )
    except DocumentEvidenceLinkNotFoundError:
        raise _not_found_error("document_evidence_link") from None
    except InvalidEvidenceLinkTransitionError:
        raise _conflict_error(
            "invalid_document_evidence_link_transition",
            "Document evidence link decision is not allowed.",
        ) from None
    return DocumentEvidenceLinkResponse.model_validate(link)


@router.patch(
    "/documents/{document_id}/links/stale",
    operation_id="markDocumentEvidenceLinksStale",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def mark_document_evidence_links_stale(
    document_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> None:
    await EvidenceService(db_session).mark_links_stale_for_document_change(
        document_id=_parse_id(document_id, resource="document")
    )


@router.patch(
    "/items/{evidence_id}/links/stale",
    operation_id="markEvidenceLinksStale",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def mark_evidence_links_stale(
    evidence_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> None:
    try:
        await EvidenceService(db_session).mark_links_stale_for_evidence_change(
            evidence_id=_parse_id(evidence_id, resource="evidence_item")
        )
    except EvidenceItemNotFoundError:
        raise _not_found_error("evidence_item") from None


@router.patch(
    "/links/{link_id}/freshness-review",
    operation_id="reviewDocumentEvidenceLinkFreshness",
    response_model=DocumentEvidenceLinkResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def review_document_evidence_link_freshness(
    link_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentEvidenceLinkResponse:
    try:
        link = await EvidenceService(db_session).review_document_evidence_freshness(
            link_id=_parse_id(link_id, resource="document_evidence_link"),
            reviewed_by_id=current_user.id,
        )
    except DocumentEvidenceLinkNotFoundError:
        raise _not_found_error("document_evidence_link") from None
    except InvalidFreshnessReviewError:
        raise _conflict_error(
            "invalid_document_evidence_freshness_review",
            "Document evidence link freshness review is not allowed.",
        ) from None
    return DocumentEvidenceLinkResponse.model_validate(link)
