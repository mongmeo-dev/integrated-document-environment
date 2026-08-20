from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.domains.auth.schemas import ApiError
from ide_api.domains.documents.router import get_object_storage
from ide_api.domains.latex.schemas import (
    ConversionReviewCreate,
    LatexProjectResponse,
    LatexSourceRevisionCreate,
)
from ide_api.domains.latex.service import (
    LatexPersistenceError,
    LatexProcessingError,
    LatexProjectNotFoundError,
    LatexProjectService,
    LatexServiceError,
    LatexStorageError,
    LatexTransitionError,
)
from ide_api.infrastructure.object_storage import ObjectStorage

router = APIRouter(prefix="/documents", tags=["latex"])
ObjectStorageDependency = Annotated[ObjectStorage, Depends(get_object_storage)]


async def _project_service(
    db_session: DbSession, object_storage: ObjectStorageDependency
) -> LatexProjectService:
    return LatexProjectService(db_session, object_storage)


ProjectServiceDependency = Annotated[LatexProjectService, Depends(_project_service)]


def _document_id(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(code="document_not_found", message="Document not found.").model_dump(),
        ) from None


def _raise_service_error(error: LatexServiceError) -> None:
    if isinstance(error, LatexProjectNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, LatexTransitionError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(error, LatexProcessingError):
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif isinstance(error, (LatexStorageError, LatexPersistenceError)):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    raise HTTPException(
        status_code=status_code,
        detail=ApiError(code=error.code, message=error.message).model_dump(),
    ) from None


@router.get(
    "/{document_id}/latex",
    operation_id="getLatexProject",
    response_model=LatexProjectResponse,
    responses={
        401: {"model": ApiError},
        404: {"model": ApiError},
        422: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def get_latex_project(
    document_id: str, _: CurrentUser, service: ProjectServiceDependency
) -> LatexProjectResponse:
    try:
        return await service.get_project(_document_id(document_id))
    except LatexServiceError as error:
        _raise_service_error(error)


@router.post(
    "/{document_id}/latex/revisions",
    operation_id="createLatexSourceRevision",
    response_model=LatexProjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ApiError},
        404: {"model": ApiError},
        409: {"model": ApiError},
        422: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def create_latex_source_revision(
    document_id: str,
    payload: LatexSourceRevisionCreate,
    current_user: CurrentUser,
    service: ProjectServiceDependency,
) -> LatexProjectResponse:
    try:
        return await service.create_source_revision(
            _document_id(document_id), payload, current_user
        )
    except LatexServiceError as error:
        _raise_service_error(error)


@router.post(
    "/{document_id}/latex/conversion-reviews",
    operation_id="reviewLatexConversion",
    response_model=LatexProjectResponse,
    responses={
        401: {"model": ApiError},
        404: {"model": ApiError},
        409: {"model": ApiError},
        422: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def review_latex_conversion(
    document_id: str,
    payload: ConversionReviewCreate,
    current_user: CurrentUser,
    service: ProjectServiceDependency,
) -> LatexProjectResponse:
    try:
        return await service.review_conversion(_document_id(document_id), payload, current_user)
    except LatexServiceError as error:
        _raise_service_error(error)


@router.get(
    "/{document_id}/latex/preview",
    operation_id="getLatexPreview",
    responses={
        401: {"model": ApiError},
        404: {"model": ApiError},
        422: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def get_latex_preview(
    document_id: str, _: CurrentUser, service: ProjectServiceDependency
) -> Response:
    try:
        pdf, filename = await service.get_preview(_document_id(document_id))
    except LatexServiceError as error:
        _raise_service_error(error)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get(
    "/{document_id}/latex/bundle",
    operation_id="getLatexBundle",
    responses={
        401: {"model": ApiError},
        404: {"model": ApiError},
        422: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def get_latex_bundle(
    document_id: str, _: CurrentUser, service: ProjectServiceDependency
) -> Response:
    try:
        bundle, filename = await service.get_bundle(_document_id(document_id))
    except LatexServiceError as error:
        _raise_service_error(error)
    return Response(
        content=bundle,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
