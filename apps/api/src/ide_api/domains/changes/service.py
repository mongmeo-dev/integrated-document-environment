from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ide_api.domains.changes.models import ChangeComment, ChangeProposal, ChangeRequest
from ide_api.domains.changes.repository import ChangeRequestRepository
from ide_api.domains.changes.schemas import (
    ChangeCommentCreate,
    ChangeCommentStatus,
    ChangeProposalCreate,
    ChangeProposalStatus,
    ChangeRequestCreate,
    ChangeRequestResponse,
    ChangeRequestStatus,
)


class ChangeRequestNotFoundError(Exception):
    pass


class ChangeProposalNotFoundError(Exception):
    pass


class ChangeCommentNotFoundError(Exception):
    pass


class InvalidChangeRequestTransitionError(Exception):
    pass


class InvalidChangeProposalTransitionError(Exception):
    pass


class UnauthorizedChangeCommentTransitionError(Exception):
    pass


_REQUEST_TRANSITIONS: dict[ChangeRequestStatus, set[ChangeRequestStatus]] = {
    ChangeRequestStatus.OPEN: {ChangeRequestStatus.IN_REVIEW, ChangeRequestStatus.REJECTED},
    ChangeRequestStatus.IN_REVIEW: {
        ChangeRequestStatus.ACCEPTED,
        ChangeRequestStatus.REJECTED,
        ChangeRequestStatus.REVISION_REQUESTED,
    },
    ChangeRequestStatus.REVISION_REQUESTED: {
        ChangeRequestStatus.IN_REVIEW,
        ChangeRequestStatus.REJECTED,
    },
    ChangeRequestStatus.ACCEPTED: set(),
    ChangeRequestStatus.REJECTED: set(),
}
_PROPOSAL_DECISIONS = {
    ChangeProposalStatus.ACCEPTED,
    ChangeProposalStatus.REJECTED,
    ChangeProposalStatus.REVISION_REQUESTED,
}


class ChangeRequestService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = ChangeRequestRepository(session)

    async def create_change_request(
        self,
        *,
        requester_id: UUID,
        data: ChangeRequestCreate,
    ) -> ChangeRequest:
        change_request = ChangeRequest(
            document_id=data.document_id,
            requester_id=requester_id,
            title=data.title,
            description=data.description,
            assignee_id=data.assignee_id,
            status=ChangeRequestStatus.OPEN.value,
        )
        self._repository.add(change_request)
        await self._session.commit()
        return change_request

    async def list_change_requests(self, *, document_id: UUID) -> list[ChangeRequest]:
        return await self._repository.list_by_document_id(document_id)

    async def get_change_request(self, *, change_request_id: UUID) -> ChangeRequestResponse:
        change_request = await self._get_change_request_with_proposals(change_request_id)
        return ChangeRequestResponse.model_validate(change_request)

    async def create_proposal(
        self,
        *,
        change_request_id: UUID,
        data: ChangeProposalCreate,
    ) -> ChangeProposal:
        await self._get_change_request_with_proposals(change_request_id)
        proposal = ChangeProposal(
            change_request_id=change_request_id,
            proposed_text=data.proposed_text,
            rationale=data.rationale,
            status=ChangeProposalStatus.CANDIDATE.value,
        )
        self._repository.add(proposal)
        await self._session.commit()
        return proposal

    async def create_comment(
        self,
        *,
        change_request_id: UUID,
        author_id: UUID,
        data: ChangeCommentCreate,
    ) -> ChangeComment:
        await self._get_change_request_with_details(change_request_id)
        comment = ChangeComment(
            change_request_id=change_request_id,
            author_id=author_id,
            assignee_id=data.assignee_id,
            body=data.body,
            status=ChangeCommentStatus.OPEN.value,
        )
        self._session.add(comment)
        await self._session.commit()
        return comment

    async def list_comments(
        self,
        *,
        change_request_id: UUID,
        assignee_id: UUID | None = None,
        status: ChangeCommentStatus | None = None,
    ) -> list[ChangeComment]:
        await self._get_change_request_with_details(change_request_id)
        statement = (
            select(ChangeComment)
            .where(ChangeComment.change_request_id == change_request_id)
            .order_by(ChangeComment.created_at.asc())
        )
        if assignee_id is not None:
            statement = statement.where(ChangeComment.assignee_id == assignee_id)
        if status is not None:
            statement = statement.where(ChangeComment.status == status.value)
        result = await self._session.execute(statement)
        return list(result.scalars())

    async def transition_comment(
        self,
        *,
        change_request_id: UUID,
        comment_id: UUID,
        status: ChangeCommentStatus,
        actor_id: UUID,
    ) -> ChangeComment:
        comment = await self._get_comment(
            change_request_id=change_request_id,
            comment_id=comment_id,
        )
        if actor_id not in {comment.author_id, comment.assignee_id}:
            raise UnauthorizedChangeCommentTransitionError
        if ChangeCommentStatus(comment.status) is status:
            return comment

        comment.status = status.value
        if status is ChangeCommentStatus.RESOLVED:
            comment.resolved_by_id = actor_id
            comment.resolved_at = datetime.now(UTC)
        else:
            comment.resolved_by_id = None
            comment.resolved_at = None
        await self._session.commit()
        return comment

    async def transition_change_request(
        self,
        *,
        change_request_id: UUID,
        status: ChangeRequestStatus,
    ) -> ChangeRequest:
        change_request = await self._get_change_request_with_proposals(change_request_id)
        current_status = ChangeRequestStatus(change_request.status)
        if status not in _REQUEST_TRANSITIONS[current_status]:
            raise InvalidChangeRequestTransitionError

        change_request.status = status.value
        await self._session.commit()
        return change_request

    async def decide_proposal(
        self,
        *,
        change_request_id: UUID,
        proposal_id: UUID,
        status: ChangeProposalStatus,
        decided_by_id: UUID,
    ) -> ChangeProposal:
        change_request = await self._get_change_request_with_proposals(change_request_id)
        proposal = next((item for item in change_request.proposals if item.id == proposal_id), None)
        if proposal is None:
            raise ChangeProposalNotFoundError
        if ChangeProposalStatus(proposal.status) is not ChangeProposalStatus.CANDIDATE:
            raise InvalidChangeProposalTransitionError
        if status not in _PROPOSAL_DECISIONS:
            raise InvalidChangeProposalTransitionError

        proposal.status = status.value
        proposal.decided_at = datetime.now(UTC)
        proposal.decided_by_id = decided_by_id

        # Accepting a proposal selects external-edit input only. It never mutates
        # document approval or completion state.
        await self._session.commit()
        return proposal

    async def _get_change_request_with_proposals(self, change_request_id: UUID) -> ChangeRequest:
        return await self._get_change_request_with_details(change_request_id)

    async def _get_change_request_with_details(self, change_request_id: UUID) -> ChangeRequest:
        result = await self._session.execute(
            select(ChangeRequest)
            .options(
                selectinload(ChangeRequest.proposals),
                selectinload(ChangeRequest.comments),
            )
            .where(ChangeRequest.id == change_request_id)
        )
        change_request = result.scalar_one_or_none()
        if change_request is None:
            raise ChangeRequestNotFoundError
        return change_request

    async def _get_comment(
        self,
        *,
        change_request_id: UUID,
        comment_id: UUID,
    ) -> ChangeComment:
        result = await self._session.execute(
            select(ChangeComment).where(
                ChangeComment.id == comment_id,
                ChangeComment.change_request_id == change_request_id,
            )
        )
        comment = result.scalar_one_or_none()
        if comment is None:
            raise ChangeCommentNotFoundError
        return comment
