from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.domains.auth.schemas import ApiError
from ide_api.domains.impacts.schemas import (
    DocumentCandidatesResponse,
    DocumentImpactCandidateCreate,
    DocumentImpactCandidateResponse,
    DocumentRelationshipCandidateCreate,
    DocumentRelationshipCandidateResponse,
    RelationshipAnalysisRunResponse,
)
from ide_api.domains.impacts.service import (
    DocumentImpactNotFoundError,
    DocumentRelationshipNotFoundError,
    ImpactService,
    InvalidCandidateTransitionError,
    InvalidModificationDecisionError,
    RelationshipAnalysisRunNotFoundError,
)

router = APIRouter(prefix="/impacts", tags=["impacts"])


def _parse_id(value: str, *, resource: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiError(
                code=f"{resource}_not_found",
                message=f"{resource.replace('_', ' ').capitalize()} not found.",
            ).model_dump(),
        ) from None


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


@router.get(
    "/documents/{document_id}",
    operation_id="listDocumentImpactCandidates",
    response_model=DocumentCandidatesResponse,
    responses={401: {"model": ApiError}},
)
async def list_document_candidates(
    document_id: UUID,
    db_session: DbSession,
    _: CurrentUser,
) -> DocumentCandidatesResponse:
    return await ImpactService(db_session).list_document_candidates(document_id=document_id)


@router.get(
    "/documents/{document_id}/analysis",
    operation_id="getLatestDocumentRelationshipAnalysis",
    response_model=RelationshipAnalysisRunResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def get_latest_relationship_analysis(
    document_id: UUID,
    db_session: DbSession,
    _: CurrentUser,
) -> RelationshipAnalysisRunResponse:
    try:
        run = await ImpactService(db_session).get_latest_analysis_run(document_id=document_id)
    except RelationshipAnalysisRunNotFoundError:
        raise _not_found_error("relationship_analysis") from None
    return RelationshipAnalysisRunResponse.model_validate(run)


@router.post(
    "/relationships",
    operation_id="createRelationshipCandidate",
    response_model=DocumentRelationshipCandidateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}},
)
async def create_relationship_candidate(
    data: DocumentRelationshipCandidateCreate,
    response: Response,
    db_session: DbSession,
    _: CurrentUser,
) -> DocumentRelationshipCandidateResponse:
    relationship = await ImpactService(db_session).create_relationship_candidate(data=data)
    response.headers["Location"] = f"/api/v1/impacts/relationships/{relationship.id}"
    return DocumentRelationshipCandidateResponse.model_validate(relationship)


@router.post(
    "/candidates",
    operation_id="createImpactCandidate",
    response_model=DocumentImpactCandidateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}},
)
async def create_impact_candidate(
    data: DocumentImpactCandidateCreate,
    response: Response,
    db_session: DbSession,
    _: CurrentUser,
) -> DocumentImpactCandidateResponse:
    impact = await ImpactService(db_session).create_impact_candidate(data=data)
    response.headers["Location"] = f"/api/v1/impacts/candidates/{impact.id}"
    return DocumentImpactCandidateResponse.model_validate(impact)


@router.patch(
    "/relationships/{relationship_id}/confirm",
    operation_id="confirmRelationshipCandidate",
    response_model=DocumentRelationshipCandidateResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def confirm_relationship_candidate(
    relationship_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentRelationshipCandidateResponse:
    try:
        relationship = await ImpactService(db_session).confirm_relationship(
            relationship_id=_parse_id(relationship_id, resource="relationship_candidate"),
            decided_by_id=current_user.id,
        )
    except DocumentRelationshipNotFoundError:
        raise _not_found_error("relationship_candidate") from None
    except InvalidCandidateTransitionError:
        raise _conflict_error(
            "invalid_relationship_candidate_transition",
            "Relationship candidate decision is not allowed.",
        ) from None
    return DocumentRelationshipCandidateResponse.model_validate(relationship)


@router.patch(
    "/relationships/{relationship_id}/reject",
    operation_id="rejectRelationshipCandidate",
    response_model=DocumentRelationshipCandidateResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def reject_relationship_candidate(
    relationship_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentRelationshipCandidateResponse:
    try:
        relationship = await ImpactService(db_session).reject_relationship(
            relationship_id=_parse_id(relationship_id, resource="relationship_candidate"),
            decided_by_id=current_user.id,
        )
    except DocumentRelationshipNotFoundError:
        raise _not_found_error("relationship_candidate") from None
    except InvalidCandidateTransitionError:
        raise _conflict_error(
            "invalid_relationship_candidate_transition",
            "Relationship candidate decision is not allowed.",
        ) from None
    return DocumentRelationshipCandidateResponse.model_validate(relationship)


@router.patch(
    "/candidates/{impact_id}/confirm",
    operation_id="confirmImpactCandidate",
    response_model=DocumentImpactCandidateResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def confirm_impact_candidate(
    impact_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentImpactCandidateResponse:
    try:
        impact = await ImpactService(db_session).confirm_impact(
            impact_id=_parse_id(impact_id, resource="impact_candidate"),
            decided_by_id=current_user.id,
        )
    except DocumentImpactNotFoundError:
        raise _not_found_error("impact_candidate") from None
    except InvalidCandidateTransitionError:
        raise _conflict_error(
            "invalid_impact_candidate_transition", "Impact candidate decision is not allowed."
        ) from None
    return DocumentImpactCandidateResponse.model_validate(impact)


@router.patch(
    "/candidates/{impact_id}/reject",
    operation_id="rejectImpactCandidate",
    response_model=DocumentImpactCandidateResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def reject_impact_candidate(
    impact_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentImpactCandidateResponse:
    try:
        impact = await ImpactService(db_session).reject_impact(
            impact_id=_parse_id(impact_id, resource="impact_candidate"),
            decided_by_id=current_user.id,
        )
    except DocumentImpactNotFoundError:
        raise _not_found_error("impact_candidate") from None
    except InvalidCandidateTransitionError:
        raise _conflict_error(
            "invalid_impact_candidate_transition", "Impact candidate decision is not allowed."
        ) from None
    return DocumentImpactCandidateResponse.model_validate(impact)


@router.patch(
    "/candidates/{impact_id}/modification-required",
    operation_id="markImpactModificationRequired",
    response_model=DocumentImpactCandidateResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def mark_impact_modification_required(
    impact_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentImpactCandidateResponse:
    try:
        impact = await ImpactService(db_session).mark_modification_required(
            impact_id=_parse_id(impact_id, resource="impact_candidate"),
            decided_by_id=current_user.id,
        )
    except DocumentImpactNotFoundError:
        raise _not_found_error("impact_candidate") from None
    except InvalidModificationDecisionError:
        raise _conflict_error(
            "invalid_modification_decision", "Impact modification decision is not allowed."
        ) from None
    return DocumentImpactCandidateResponse.model_validate(impact)


@router.patch(
    "/candidates/{impact_id}/modification-not-required",
    operation_id="markImpactModificationNotRequired",
    response_model=DocumentImpactCandidateResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def mark_impact_modification_not_required(
    impact_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> DocumentImpactCandidateResponse:
    try:
        impact = await ImpactService(db_session).mark_modification_not_required(
            impact_id=_parse_id(impact_id, resource="impact_candidate"),
            decided_by_id=current_user.id,
        )
    except DocumentImpactNotFoundError:
        raise _not_found_error("impact_candidate") from None
    except InvalidModificationDecisionError:
        raise _conflict_error(
            "invalid_modification_decision", "Impact modification decision is not allowed."
        ) from None
    return DocumentImpactCandidateResponse.model_validate(impact)
