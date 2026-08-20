"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { impactsApi } from "@/api/client";
import {
  CandidateStatus,
  type DocumentImpactCandidateResponse,
} from "@/api/generated";

import styles from "./relations.module.css";

type RelationshipType = "추적 관계" | "의존 관계" | "검증 근거" | "영향 후보";
type Depth = 1 | 2 | 3;
type Impact = {
  id: string;
  type: RelationshipType;
  depth: Depth | null;
  sourceDocument: string;
  sourceLocation: string;
  targetDocument: string;
  targetLocation: string;
  reason: string;
  proposedModification: string;
  status: (typeof CandidateStatus)[keyof typeof CandidateStatus];
  modificationRequired: boolean | null;
};

const statusLabel = {
  [CandidateStatus.Candidate]: "후보",
  [CandidateStatus.Confirmed]: "확정",
  [CandidateStatus.Rejected]: "반려",
};

function abbreviatedDocumentId(documentId: string) {
  return `${documentId.slice(0, 8)}…${documentId.slice(-4)}`;
}

function mapImpact(impact: DocumentImpactCandidateResponse): Impact {
  return {
    id: impact.id,
    type: "영향 후보",
    depth: null,
    sourceDocument: abbreviatedDocumentId(impact.source_document_id),
    sourceLocation: impact.source_location,
    targetDocument: abbreviatedDocumentId(impact.target_document_id),
    targetLocation: impact.target_location,
    reason: impact.reason,
    proposedModification: impact.proposed_modification,
    status: impact.status,
    modificationRequired: impact.modification_required,
  };
}

function StatusIcon({ status }: { status: Impact["status"] }) {
  if (status === CandidateStatus.Confirmed) {
    return (
      <span aria-hidden="true" className={styles.confirmedIcon}>
        ●
      </span>
    );
  }
  if (status === CandidateStatus.Rejected) {
    return (
      <span aria-hidden="true" className={styles.rejectedIcon}>
        ×
      </span>
    );
  }
  return (
    <span aria-hidden="true" className={styles.candidateIcon}>
      ⋯
    </span>
  );
}

export function ImpactWorkspace({ documentId }: { documentId: string }) {
  const [impacts, setImpacts] = useState<Impact[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<RelationshipType | "전체">(
    "전체",
  );
  const [statusFilter, setStatusFilter] = useState<"전체" | Impact["status"]>(
    "전체",
  );
  const [depthFilter, setDepthFilter] = useState<"전체" | Depth>("전체");
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestVersion = useRef(0);

  const loadImpacts = useCallback(
    async (preferredId?: string) => {
      const requestId = ++requestVersion.current;
      setLoading(true);
      setError(null);
      try {
        const response = await impactsApi.listDocumentImpactCandidates({
          documentId,
        });
        if (requestVersion.current !== requestId) return;
        const mappedImpacts = (response.data.impacts ?? []).map(mapImpact);
        setImpacts(mappedImpacts);
        setSelectedId(
          mappedImpacts.some((impact) => impact.id === preferredId)
            ? (preferredId ?? null)
            : (mappedImpacts[0]?.id ?? null),
        );
      } catch {
        if (requestVersion.current !== requestId) return;
        setImpacts([]);
        setSelectedId(null);
        setError("영향 후보를 불러오지 못했습니다. 다시 시도해 주세요.");
      } finally {
        if (requestVersion.current === requestId) setLoading(false);
      }
    },
    [documentId],
  );

  useEffect(() => {
    void loadImpacts();
  }, [loadImpacts]);

  const visibleImpacts = useMemo(
    () =>
      impacts.filter(
        (impact) =>
          (typeFilter === "전체" || impact.type === typeFilter) &&
          (statusFilter === "전체" || impact.status === statusFilter) &&
          (depthFilter === "전체" || impact.depth === depthFilter),
      ),
    [depthFilter, impacts, statusFilter, typeFilter],
  );
  const selectedImpact =
    impacts.find((impact) => impact.id === selectedId) ?? null;

  async function performAction(
    action: "confirm" | "reject" | "required" | "not-required",
  ) {
    if (!selectedImpact) return;
    setPendingAction(action);
    setError(null);
    try {
      if (action === "confirm")
        await impactsApi.confirmImpactCandidate({
          impactId: selectedImpact.id,
        });
      if (action === "reject")
        await impactsApi.rejectImpactCandidate({ impactId: selectedImpact.id });
      if (action === "required")
        await impactsApi.markImpactModificationRequired({
          impactId: selectedImpact.id,
        });
      if (action === "not-required")
        await impactsApi.markImpactModificationNotRequired({
          impactId: selectedImpact.id,
        });

      await loadImpacts(selectedImpact.id);
    } catch {
      setError("조치를 완료하지 못했습니다. 다시 시도해 주세요.");
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <div className={styles.app}>
      <div className={styles.workspace}>
        <aside className={styles.filters} aria-label="관계 필터">
          <div className={styles.panelHeading}>
            <div>
              <p className={styles.eyebrow}>변경 전파 검토</p>
              <h1>관계·영향</h1>
            </div>
          </div>
          <fieldset>
            <legend>관계 유형</legend>
            {(
              [
                "전체",
                "추적 관계",
                "의존 관계",
                "검증 근거",
                "영향 후보",
              ] as const
            ).map((value) => (
              <label key={value}>
                <input
                  checked={typeFilter === value}
                  name="type"
                  onChange={() => setTypeFilter(value)}
                  type="radio"
                />
                {value}
              </label>
            ))}
          </fieldset>
          <fieldset>
            <legend>후보 상태</legend>
            {(
              [
                "전체",
                CandidateStatus.Candidate,
                CandidateStatus.Confirmed,
                CandidateStatus.Rejected,
              ] as const
            ).map((value) => (
              <label key={value}>
                <input
                  checked={statusFilter === value}
                  name="status"
                  onChange={() => setStatusFilter(value)}
                  type="radio"
                />
                {value === "전체" ? value : statusLabel[value]}
              </label>
            ))}
          </fieldset>
          <fieldset>
            <legend>영향 깊이</legend>
            {(["전체", 1, 2, 3] as const).map((value) => (
              <label key={String(value)}>
                <input
                  checked={depthFilter === value}
                  name="depth"
                  onChange={() => setDepthFilter(value)}
                  type="radio"
                />
                {value === "전체" ? value : `${value}단계`}
              </label>
            ))}
          </fieldset>
        </aside>

        <section
          className={styles.mainPanel}
          aria-labelledby="relation-heading"
        >
          <div className={styles.mainHeading}>
            <div>
              <p className={styles.eyebrow}>
                관계 후보 {visibleImpacts.length}건
              </p>
              <h2 id="relation-heading">변경 전파 경로</h2>
            </div>
            <fieldset aria-label="관계 상태 범례" className={styles.legend}>
              <span>
                <i className={styles.solidLine} aria-hidden="true" />
                확정 실선
              </span>
              <span>
                <i className={styles.dashedLine} aria-hidden="true" />
                후보 점선
              </span>
              <span>
                <StatusIcon status={CandidateStatus.Candidate} />
                재검토 경고
              </span>
            </fieldset>
          </div>

          <ol
            className={styles.relationshipList}
            id="relationship-list"
            aria-label="관계 후보 목록"
          >
            {visibleImpacts.map((impact) => (
              <li key={impact.id}>
                <button
                  aria-current={
                    impact.id === selectedImpact?.id ? "true" : undefined
                  }
                  className={
                    impact.id === selectedImpact?.id
                      ? styles.selected
                      : undefined
                  }
                  onClick={() => {
                    setSelectedId(impact.id);
                    setError(null);
                  }}
                  type="button"
                >
                  <StatusIcon status={impact.status} />
                  <span className={styles.listCopy}>
                    <strong>{impact.sourceDocument}</strong>
                    <span>
                      {impact.sourceLocation} → {impact.targetDocument}
                    </span>
                    <small>
                      {impact.type} ·{" "}
                      {impact.depth === null
                        ? "깊이 정보 없음"
                        : `${impact.depth}단계`}{" "}
                      · {statusLabel[impact.status]}
                    </small>
                  </span>
                  {impact.modificationRequired === null && (
                    <span className={styles.reviewWarning}>재검토</span>
                  )}
                </button>
              </li>
            ))}
            {visibleImpacts.length === 0 && (
              <li className={styles.empty}>
                {loading
                  ? "영향 후보를 불러오는 중입니다."
                  : impacts.length > 0
                    ? "선택한 필터에 맞는 관계가 없습니다."
                    : "영향 후보가 없습니다."}
              </li>
            )}
          </ol>
        </section>

        <aside
          className={styles.detail}
          aria-live="polite"
          aria-label="선택한 관계 상세"
        >
          {selectedImpact ? (
            <>
              <p className={styles.eyebrow}>선택 관계</p>
              <div className={styles.detailTitle}>
                <StatusIcon status={selectedImpact.status} />
                <h2>{selectedImpact.type}</h2>
              </div>
              <p className={styles.statusText}>
                {statusLabel[selectedImpact.status]} · 영향 깊이{" "}
                {selectedImpact.depth === null
                  ? "정보 없음"
                  : `${selectedImpact.depth}단계`}
              </p>
              <dl>
                <div>
                  <dt>관련 문서</dt>
                  <dd>
                    {selectedImpact.sourceDocument}
                    <br />
                    {selectedImpact.targetDocument}
                  </dd>
                </div>
                <div>
                  <dt>PRD 위치</dt>
                  <dd>
                    {selectedImpact.sourceLocation}
                    <br />→ {selectedImpact.targetLocation}
                  </dd>
                </div>
                <div>
                  <dt>관계 이유</dt>
                  <dd>{selectedImpact.reason}</dd>
                </div>
                <div>
                  <dt>수정 필요 여부</dt>
                  <dd>
                    {selectedImpact.modificationRequired === null
                      ? "결정 전 · 재검토 필요"
                      : selectedImpact.modificationRequired
                        ? "수정 필요"
                        : "수정 불필요"}
                  </dd>
                </div>
              </dl>
              <section
                className={styles.proposal}
                aria-labelledby="proposal-title"
              >
                <h3 id="proposal-title">수정안 후보</h3>
                <p>{selectedImpact.proposedModification}</p>
              </section>
            </>
          ) : (
            <p className={styles.statusText}>영향 후보를 선택하세요.</p>
          )}
          {error && (
            <div className={styles.error} role="alert">
              <p>{error}</p>
              <button onClick={() => void loadImpacts()} type="button">
                다시 시도
              </button>
            </div>
          )}
          {selectedImpact && (
            <fieldset aria-label="관계 검토 조치" className={styles.actions}>
              <button
                disabled={
                  pendingAction !== null ||
                  selectedImpact.status !== CandidateStatus.Candidate
                }
                onClick={() => performAction("confirm")}
                type="button"
              >
                {pendingAction === "confirm" ? "확정 중…" : "명시적으로 확정"}
              </button>
              <button
                disabled={
                  pendingAction !== null ||
                  selectedImpact.status !== CandidateStatus.Candidate
                }
                onClick={() => performAction("reject")}
                type="button"
              >
                {pendingAction === "reject" ? "반려 중…" : "후보 반려"}
              </button>
              <button
                disabled={pendingAction !== null}
                onClick={() => performAction("required")}
                type="button"
              >
                {pendingAction === "required" ? "저장 중…" : "수정 필요"}
              </button>
              <button
                disabled={pendingAction !== null}
                onClick={() => performAction("not-required")}
                type="button"
              >
                {pendingAction === "not-required" ? "저장 중…" : "수정 불필요"}
              </button>
            </fieldset>
          )}
          <p className={styles.actionHint}>
            자동 확정하지 않습니다. 각 조치 성공 후 목록을 다시 조회합니다.
          </p>
        </aside>
      </div>
    </div>
  );
}
