from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from ide_api.api.dependencies import CurrentUser, DbSession
from ide_api.domains.approvals.schemas import (
    ApprovalStepResponse,
    ApprovalStepUpdate,
    ApprovalWorkflowAuditResponse,
    ApprovalWorkflowCreate,
    ApprovalWorkflowResponse,
)
from ide_api.domains.approvals.service import (
    ApprovalNotAuthorizedError,
    ApprovalService,
    ApprovalStepImmutableError,
    ApprovalStepNotFoundError,
    ApprovalStepSequenceError,
    ApprovalWorkflowAlreadyExistsError,
    ApprovalWorkflowNotFoundError,
    InvalidApprovalTransitionError,
    InvalidApprovalWorkflowError,
)
from ide_api.domains.auth.schemas import ApiError

router = APIRouter(prefix="/approvals", tags=["approvals"])


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


@router.post(
    "",
    operation_id="createApprovalWorkflow",
    response_model=ApprovalWorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ApiError}, 409: {"model": ApiError}},
)
async def create_approval_workflow(
    data: ApprovalWorkflowCreate,
    response: Response,
    db_session: DbSession,
    _: CurrentUser,
) -> ApprovalWorkflowResponse:
    try:
        workflow = await ApprovalService(db_session).create_workflow(data=data)
    except ApprovalWorkflowAlreadyExistsError:
        raise _conflict_error(
            "approval_workflow_already_exists",
            "An approval workflow already exists for this document.",
        ) from None
    except ApprovalStepSequenceError, InvalidApprovalWorkflowError:
        raise _conflict_error(
            "invalid_approval_workflow",
            "Approval workflow steps are invalid.",
        ) from None

    response.headers["Location"] = f"/api/v1/approvals/{workflow.id}"
    return ApprovalWorkflowResponse.model_validate(workflow)


@router.get(
    "/{workflow_id}",
    operation_id="getApprovalWorkflow",
    response_model=ApprovalWorkflowResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def get_approval_workflow(
    workflow_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> ApprovalWorkflowResponse:
    try:
        workflow = await ApprovalService(db_session).get_workflow(
            workflow_id=_parse_id(workflow_id, resource="approval_workflow")
        )
    except ApprovalWorkflowNotFoundError:
        raise _not_found_error("approval_workflow") from None
    return ApprovalWorkflowResponse.model_validate(workflow)


@router.get(
    "/documents/{document_id}",
    operation_id="getDocumentApprovalWorkflow",
    response_model=ApprovalWorkflowResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def get_document_approval_workflow(
    document_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> ApprovalWorkflowResponse:
    try:
        workflow = await ApprovalService(db_session).get_workflow_for_document(
            document_id=_parse_id(document_id, resource="approval_workflow")
        )
    except ApprovalWorkflowNotFoundError:
        raise _not_found_error("approval_workflow") from None
    return ApprovalWorkflowResponse.model_validate(workflow)


@router.post(
    "/{workflow_id}/start",
    operation_id="startApprovalWorkflow",
    response_model=ApprovalWorkflowResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def start_approval_workflow(
    workflow_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> ApprovalWorkflowResponse:
    try:
        workflow = await ApprovalService(db_session).start_workflow(
            workflow_id=_parse_id(workflow_id, resource="approval_workflow")
        )
    except ApprovalWorkflowNotFoundError:
        raise _not_found_error("approval_workflow") from None
    except InvalidApprovalTransitionError, InvalidApprovalWorkflowError:
        raise _conflict_error(
            "invalid_approval_workflow_transition",
            "Approval workflow transition is not allowed.",
        ) from None
    return ApprovalWorkflowResponse.model_validate(workflow)


@router.patch(
    "/steps/{step_id}",
    operation_id="updateApprovalStep",
    response_model=ApprovalStepResponse,
    responses={401: {"model": ApiError}, 404: {"model": ApiError}, 409: {"model": ApiError}},
)
async def update_approval_step(
    step_id: str,
    data: ApprovalStepUpdate,
    db_session: DbSession,
    current_user: CurrentUser,
) -> ApprovalStepResponse:
    if data.reason is None:
        raise _conflict_error(
            "approval_step_update_reason_required",
            "A reason is required when changing an approval step.",
        )
    try:
        step = await ApprovalService(db_session).update_approval_step(
            step_id=_parse_id(step_id, resource="approval_step"),
            data=data,
            actor_id=current_user.id,
        )
    except ApprovalStepNotFoundError:
        raise _not_found_error("approval_step") from None
    except ApprovalStepImmutableError:
        raise _conflict_error(
            "approval_step_immutable",
            "Completed approval steps cannot be changed.",
        ) from None
    except ApprovalStepSequenceError:
        raise _conflict_error(
            "invalid_approval_step_sequence",
            "Approval step sequence is not allowed.",
        ) from None
    except InvalidApprovalTransitionError, InvalidApprovalWorkflowError:
        raise _conflict_error(
            "invalid_approval_step_update",
            "Approval step update is not allowed.",
        ) from None
    return ApprovalStepResponse.model_validate(step)


@router.post(
    "/steps/{step_id}/approve",
    operation_id="approveApprovalStep",
    response_model=ApprovalWorkflowResponse,
    responses={
        401: {"model": ApiError},
        403: {"model": ApiError},
        404: {"model": ApiError},
        409: {"model": ApiError},
    },
)
async def approve_approval_step(
    step_id: str,
    db_session: DbSession,
    current_user: CurrentUser,
) -> ApprovalWorkflowResponse:
    try:
        workflow = await ApprovalService(db_session).approve_step(
            step_id=_parse_id(step_id, resource="approval_step"),
            actor_id=current_user.id,
        )
    except ApprovalStepNotFoundError:
        raise _not_found_error("approval_step") from None
    except ApprovalNotAuthorizedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ApiError(
                code="approval_not_authorized",
                message="Current user is not assigned to this approval step.",
            ).model_dump(),
        ) from None
    except InvalidApprovalTransitionError:
        raise _conflict_error(
            "invalid_approval_step_transition",
            "Approval step transition is not allowed.",
        ) from None
    return ApprovalWorkflowResponse.model_validate(workflow)


@router.get(
    "/{workflow_id}/audits",
    operation_id="listApprovalWorkflowAudits",
    response_model=list[ApprovalWorkflowAuditResponse],
    responses={401: {"model": ApiError}, 404: {"model": ApiError}},
)
async def list_approval_workflow_audits(
    workflow_id: str,
    db_session: DbSession,
    _: CurrentUser,
) -> list[ApprovalWorkflowAuditResponse]:
    try:
        audits = await ApprovalService(db_session).list_workflow_audits(
            workflow_id=_parse_id(workflow_id, resource="approval_workflow")
        )
    except ApprovalWorkflowNotFoundError:
        raise _not_found_error("approval_workflow") from None
    return [ApprovalWorkflowAuditResponse.model_validate(audit) for audit in audits]
