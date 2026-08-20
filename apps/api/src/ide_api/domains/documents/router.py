from collections.abc import Iterator
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.domains.auth.schemas import ApiError
from ide_api.domains.documents.schemas import DocumentResponse, DocumentStatus
from ide_api.domains.documents.service import (
    DocumentNotFoundError,
    DocumentPersistenceError,
    DocumentService,
    DocumentStorageError,
    DocumentUploadError,
)
from ide_api.domains.latex.service import (
    LatexPersistenceError,
    LatexProcessingError,
    LatexProjectNotFoundError,
    LatexProjectService,
    LatexStorageError,
)
from ide_api.infrastructure.object_storage import ObjectStorage

router = APIRouter(prefix="/documents", tags=["documents"])


def get_object_storage() -> ObjectStorage:
    return ObjectStorage()


ObjectStorageDependency = Annotated[ObjectStorage, Depends(get_object_storage)]


@router.post(
    "",
    operation_id="registerDocument",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ApiError},
        401: {"model": ApiError},
        413: {"model": ApiError},
        415: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def register_document(
    response: Response,
    db_session: DbSession,
    current_user: CurrentUser,
    object_storage: ObjectStorageDependency,
    file: Annotated[UploadFile, File()],
) -> DocumentResponse:
    try:
        document = await DocumentService(db_session, object_storage).register_original(
            upload=file,
            creator=current_user,
        )
    except DocumentUploadError as error:
        status_code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if error.code == "file_too_large"
            else (
                status.HTTP_400_BAD_REQUEST
                if error.code == "empty_file"
                else status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )
        )
        raise HTTPException(
            status_code=status_code,
            detail=ApiError(code=error.code, message=error.message).model_dump(),
        ) from None
    except DocumentStorageError, DocumentPersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ApiError(
                code="document_registration_unavailable",
                message="Document registration is temporarily unavailable.",
            ).model_dump(),
        ) from None

    response.headers["Location"] = f"/api/v1/documents/{document.id}"
    return DocumentService.to_response(document)


@router.get(
    "",
    operation_id="listDocuments",
    response_model=list[DocumentResponse],
    responses={401: {"model": ApiError}},
)
async def list_documents(
    db_session: DbSession,
    _: CurrentUser,
    document_status: Annotated[DocumentStatus | None, Query(alias="status")] = None,
    query: Annotated[str | None, Query(max_length=255)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DocumentResponse]:
    documents = await DocumentService(db_session)._repository.list_latest_versions(
        document_status=document_status,
        query=query,
        limit=limit,
        offset=offset,
    )
    return [DocumentService.to_response(document) for document in documents]


@router.get(
    "/{document_id}",
    operation_id="getDocument",
    response_model=DocumentResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def get_document(
    document_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> DocumentResponse:
    try:
        parsed_document_id = UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(code="document_not_found", message="Document not found.").model_dump(),
        ) from None

    try:
        return await DocumentService(db_session).get_document(parsed_document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(code="document_not_found", message="Document not found.").model_dump(),
        ) from None


@router.get(
    "/{document_id}/original",
    operation_id="downloadOriginalDocument",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {
                "application/octet-stream": {"schema": {"type": "string", "format": "binary"}}
            }
        },
        401: {"model": ApiError},
        404: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def download_original_document(
    document_id: str,
    db_session: DbSession,
    _: CurrentUser,
    object_storage: ObjectStorageDependency,
) -> StreamingResponse:
    try:
        parsed_document_id = UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(code="document_not_found", message="Document not found.").model_dump(),
        ) from None

    try:
        content, filename, media_type, resources = await DocumentService(
            db_session, object_storage
        ).get_original(parsed_document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(code="document_not_found", message="Document not found.").model_dump(),
        ) from None
    except DocumentStorageError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ApiError(
                code="original_download_unavailable",
                message="The stored original is temporarily unavailable.",
            ).model_dump(),
        ) from None

    def chunks() -> Iterator[bytes]:
        while chunk := content.read(1024 * 1024):
            yield chunk

    return StreamingResponse(
        chunks(),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        background=BackgroundTask(resources.close),
    )


@router.post(
    "/{document_id}/validate",
    operation_id="validateDocument",
    response_model=DocumentResponse,
    responses={
        401: {"model": ApiError},
        404: {"model": ApiError},
        422: {"model": ApiError},
        503: {"model": ApiError},
    },
)
async def validate_document(
    document_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
    object_storage: ObjectStorageDependency,
) -> DocumentResponse:
    try:
        parsed_document_id = UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(code="document_not_found", message="Document not found.").model_dump(),
        ) from None

    try:
        document = await DocumentService(db_session, object_storage).validate_original(
            parsed_document_id
        )
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(code="document_not_found", message="Document not found.").model_dump(),
        ) from None
    except DocumentStorageError, DocumentPersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ApiError(
                code="document_validation_unavailable",
                message="Document validation is temporarily unavailable.",
            ).model_dump(),
        ) from None

    if document.versions[0].input_kind in {"latex_project", "docx_import"}:
        try:
            await LatexProjectService(db_session, object_storage).ensure_initial_revision(
                parsed_document_id, current_user
            )
        except LatexProcessingError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=ApiError(code=error.code, message=error.message).model_dump(),
            ) from None
        except LatexProjectNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ApiError(
                    code="document_not_found", message="Document not found."
                ).model_dump(),
            ) from None
        except LatexStorageError, LatexPersistenceError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ApiError(
                    code="latex_initialization_unavailable",
                    message="LaTeX project initialization is temporarily unavailable.",
                ).model_dump(),
            ) from None

    return DocumentService.to_response(document)
