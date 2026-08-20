"use client";

import { useEffect, useState } from "react";

import { changesApi } from "@/api/client";
import {
  type ChangeProposalResponse,
  ChangeProposalStatus,
  type ChangeProposalStatus as ChangeProposalStatusType,
  type ChangeRequestResponse,
  ChangeRequestStatus,
  type ChangeRequestStatus as ChangeRequestStatusType,
} from "@/api/generated";

import styles from "./changes.module.css";

const statusLabels: Record<ChangeRequestStatusType, string> = {
  [ChangeRequestStatus.Open]: "접수됨",
  [ChangeRequestStatus.InReview]: "검토 중",
  [ChangeRequestStatus.Accepted]: "단계 승인됨",
  [ChangeRequestStatus.Rejected]: "반려됨",
  [ChangeRequestStatus.RevisionRequested]: "수정 요청됨",
};

const proposalStatusLabels: Record<ChangeProposalStatusType, string> = {
  [ChangeProposalStatus.Candidate]: "후보",
  [ChangeProposalStatus.Accepted]: "수락됨",
  [ChangeProposalStatus.Rejected]: "반려됨",
  [ChangeProposalStatus.RevisionRequested]: "수정 요청됨",
};

function apiErrorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "API 요청을 완료하지 못했습니다.";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function ChangeRequestWorkspace({ documentId }: { documentId: string }) {
  const [requests, setRequests] = useState<ChangeRequestResponse[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedRequest, setSelectedRequest] =
    useState<ChangeRequestResponse | null>(null);
  const [status, setStatus] = useState<ChangeRequestStatusType>(
    ChangeRequestStatus.Open,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [statusPending, setStatusPending] = useState(false);
  const [proposalPending, setProposalPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const liveDocumentId = documentId;
    let active = true;
    async function loadRequests() {
      setIsLoading(true);
      setError(null);
      setRequests([]);
      setSelectedId(null);
      setSelectedRequest(null);
      try {
        const response = await changesApi.listChangeRequests({
          documentId: liveDocumentId,
        });
        if (active) {
          setRequests(response.data);
          setSelectedId(response.data[0]?.id ?? null);
        }
      } catch (requestError) {
        if (active)
          setError(
            `변경 요청 목록을 불러오지 못했습니다: ${apiErrorMessage(requestError)}`,
          );
      } finally {
        if (active) setIsLoading(false);
      }
    }
    void loadRequests();
    return () => {
      active = false;
    };
  }, [documentId]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedRequest(null);
      return;
    }
    const liveSelectedId = selectedId;
    let active = true;
    async function loadRequest() {
      setDetailLoading(true);
      setError(null);
      try {
        const response = await changesApi.getChangeRequest({
          changeRequestId: liveSelectedId,
        });
        if (active) {
          setSelectedRequest(response.data);
          setStatus(response.data.status);
        }
      } catch (requestError) {
        if (active)
          setError(
            `변경 요청 상세를 불러오지 못했습니다: ${apiErrorMessage(requestError)}`,
          );
      } finally {
        if (active) setDetailLoading(false);
      }
    }
    void loadRequest();
    return () => {
      active = false;
    };
  }, [selectedId]);

  function selectRequest(request: ChangeRequestResponse) {
    setSelectedId(request.id);
    setError(null);
  }

  async function updateRequestStatus() {
    if (!selectedRequest) return;
    setStatusPending(true);
    setError(null);
    try {
      const response = await changesApi.transitionChangeRequest({
        changeRequestId: selectedRequest.id,
        changeRequestTransition: { status },
      });
      setSelectedRequest((current) =>
        current
          ? {
              ...current,
              ...response.data,
              proposals: response.data.proposals ?? current.proposals,
            }
          : response.data,
      );
      setRequests((current) =>
        current.map((request) =>
          request.id === response.data.id
            ? { ...request, ...response.data }
            : request,
        ),
      );
    } catch (requestError) {
      setError(
        `요청 상태를 변경하지 못했습니다: ${apiErrorMessage(requestError)}`,
      );
    } finally {
      setStatusPending(false);
    }
  }

  async function decideProposal(
    proposal: ChangeProposalResponse,
    proposalStatus: ChangeProposalStatusType,
  ) {
    if (!selectedRequest) return;
    setProposalPending(proposal.id);
    setError(null);
    try {
      const response = await changesApi.decideChangeProposal({
        changeRequestId: selectedRequest.id,
        proposalId: proposal.id,
        changeProposalDecision: { status: proposalStatus },
      });
      setSelectedRequest((current) =>
        current
          ? {
              ...current,
              proposals: current.proposals?.map((item) =>
                item.id === response.data.id ? response.data : item,
              ),
            }
          : current,
      );
    } catch (requestError) {
      setError(
        `수정안을 처리하지 못했습니다: ${apiErrorMessage(requestError)}`,
      );
    } finally {
      setProposalPending(null);
    }
  }

  if (isLoading)
    return (
      <div className={styles.workspace}>
        <p className={styles.empty} aria-live="polite">
          변경 요청을 불러오는 중입니다.
        </p>
      </div>
    );
  if (error && !selectedRequest)
    return (
      <div className={styles.workspace}>
        <p className={styles.error} role="alert">
          {error}
        </p>
      </div>
    );
  if (!selectedRequest && requests.length === 0)
    return (
      <div className={styles.workspace}>
        <p className={styles.empty}>이 문서에는 변경 요청이 없습니다.</p>
      </div>
    );
  if (!selectedRequest)
    return (
      <div className={styles.workspace}>
        <p className={styles.empty}>변경 요청 상세를 불러오는 중입니다.</p>
      </div>
    );

  const proposals = selectedRequest.proposals ?? [];
  return (
    <div className={styles.workspace}>
      <aside
        className={styles.requestList}
        id="change-requests"
        aria-label="변경 요청 목록"
      >
        <div className={styles.listHeading}>
          <div>
            <p className={styles.eyebrow}>문서 ID: {documentId}</p>
            <h1>변경 요청 검토</h1>
          </div>
        </div>
        <ol>
          {requests.map((request) => (
            <li key={request.id}>
              <button
                aria-current={
                  request.id === selectedRequest.id ? "true" : undefined
                }
                className={
                  request.id === selectedRequest.id
                    ? styles.selectedRequest
                    : undefined
                }
                onClick={() => selectRequest(request)}
                type="button"
              >
                <span>{request.id}</span>
                <strong>{request.title}</strong>
                <small>
                  {statusLabels[request.status]} ·{" "}
                  {formatDate(request.updated_at)}
                </small>
              </button>
            </li>
          ))}
        </ol>
      </aside>
      <section className={styles.detail} aria-live="polite">
        <div className={styles.breadcrumb}>문서 / 변경 요청 검토</div>
        <div className={styles.detailHeading}>
          <div>
            <p className={styles.eyebrow}>{selectedRequest.id}</p>
            <h2>{selectedRequest.title}</h2>
            <p>{selectedRequest.description}</p>
          </div>
          <span className={styles.status}>
            {statusLabels[selectedRequest.status]}
          </span>
        </div>
        <dl className={styles.metadata}>
          <div>
            <dt>담당자</dt>
            <dd>{selectedRequest.assignee_id ?? "미지정"}</dd>
          </div>
          <div>
            <dt>요청자</dt>
            <dd>{selectedRequest.requester_id}</dd>
          </div>
          <div>
            <dt>마지막 변경</dt>
            <dd>{formatDate(selectedRequest.updated_at)}</dd>
          </div>
        </dl>
        <section
          className={styles.statusControl}
          aria-label="변경 요청 단계 상태"
        >
          <div>
            <h3>요청 단계</h3>
            <p>후보 수락과 별도로 변경 요청 자체의 단계를 관리합니다.</p>
          </div>
          <label>
            <span>상태 선택</span>
            <select
              value={status}
              onChange={(event) =>
                setStatus(event.target.value as ChangeRequestStatusType)
              }
            >
              {Object.values(ChangeRequestStatus).map((value) => (
                <option key={value} value={value}>
                  {statusLabels[value]}
                </option>
              ))}
            </select>
          </label>
          <button
            disabled={statusPending || detailLoading}
            onClick={updateRequestStatus}
            type="button"
          >
            {statusPending ? "상태 변경 중…" : "요청 단계 적용"}
          </button>
        </section>
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <section
          className={styles.proposals}
          aria-labelledby="proposal-heading"
        >
          <div className={styles.sectionHeading}>
            <div>
              <p className={styles.eyebrow}>수정안 후보</p>
              <h3 id="proposal-heading">검토할 변경 문구</h3>
            </div>
            <span>{proposals.length}개</span>
          </div>
          {proposals.length > 0 ? (
            <div className={styles.proposalList}>
              {proposals.map((proposal) => {
                const pending = proposalPending === proposal.id;
                return (
                  <article className={styles.proposal} key={proposal.id}>
                    <div className={styles.proposalHeading}>
                      <h4>수정안 {proposal.id}</h4>
                      <span>{proposalStatusLabels[proposal.status]}</span>
                    </div>
                    <blockquote>{proposal.proposed_text}</blockquote>
                    <p>
                      <strong>근거</strong> {proposal.rationale}
                    </p>
                    <div className={styles.actions}>
                      <button
                        disabled={pending}
                        onClick={() =>
                          decideProposal(
                            proposal,
                            ChangeProposalStatus.Accepted,
                          )
                        }
                        type="button"
                      >
                        {pending ? "처리 중…" : "수락"}
                      </button>
                      <button
                        disabled={pending}
                        onClick={() =>
                          decideProposal(
                            proposal,
                            ChangeProposalStatus.Rejected,
                          )
                        }
                        type="button"
                      >
                        반려
                      </button>
                      <button
                        disabled={pending}
                        onClick={() =>
                          decideProposal(
                            proposal,
                            ChangeProposalStatus.RevisionRequested,
                          )
                        }
                        type="button"
                      >
                        수정 재요청
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className={styles.empty}>아직 등록된 수정안 후보가 없습니다.</p>
          )}
        </section>
      </section>
    </div>
  );
}
