"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

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

const fixtureImpacts: Impact[] = [
  {
    id: "fixture-impact-041",
    type: "추적 관계",
    depth: 1,
    sourceDocument: "ND-SRS-002 · 사용자 접근 통제",
    sourceLocation: "§ 4.2, 문단 3",
    targetDocument: "ND-VAL-008 · 접근 통제 검증",
    targetLocation: "TC-12, 예상 결과",
    reason:
      "세션 만료 기준이 변경되면 검증 시나리오의 허용 시간도 함께 갱신되어야 합니다.",
    proposedModification:
      "TC-12의 비활성 시간 조건을 30분으로 수정하고 재인증 확인 단계를 추가합니다.",
    status: CandidateStatus.Candidate,
    modificationRequired: null,
  },
  {
    id: "fixture-impact-038",
    type: "의존 관계",
    depth: 1,
    sourceDocument: "ND-SRS-002 · 감사 추적",
    sourceLocation: "§ 6.1, 표 4",
    targetDocument: "ND-DS-014 · 데이터 보존 정책",
    targetLocation: "§ 3.4, 보존 기간",
    reason:
      "감사 로그 보존 기간 요구사항은 데이터 보존 정책의 기준값을 참조합니다.",
    proposedModification:
      "보존 기간을 5년으로 변경하고 조사 중 예외를 정책에 명시합니다.",
    status: CandidateStatus.Confirmed,
    modificationRequired: true,
  },
  {
    id: "fixture-impact-033",
    type: "검증 근거",
    depth: 2,
    sourceDocument: "ND-VAL-008 · 접근 통제 검증",
    sourceLocation: "TC-12, 실행 기록",
    targetDocument: "ND-RA-003 · 위험 평가",
    targetLocation: "R-17, 완화 조치",
    reason: "세션 만료 통제의 검증 결과는 R-17 위험 완화의 객관적 근거입니다.",
    proposedModification:
      "위험 평가의 검증 근거 링크를 TC-12 실행 기록으로 교체합니다.",
    status: CandidateStatus.Candidate,
    modificationRequired: false,
  },
  {
    id: "fixture-impact-027",
    type: "추적 관계",
    depth: 3,
    sourceDocument: "ND-DS-014 · 데이터 보존 정책",
    sourceLocation: "§ 3.4, 보존 기간",
    targetDocument: "ND-QA-005 · 정기 검토 절차",
    targetLocation: "§ 5.2, 점검 항목",
    reason:
      "보존 기간 변경이 정기 점검의 표본 기간에 영향을 주는지 재검토가 필요합니다.",
    proposedModification: "표본 기간 산정 기준에 5년 보존 정책을 반영합니다.",
    status: CandidateStatus.Candidate,
    modificationRequired: null,
  },
];

const statusLabel = {
  [CandidateStatus.Candidate]: "후보",
  [CandidateStatus.Confirmed]: "확정",
  [CandidateStatus.Rejected]: "반려",
};

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "API 요청을 완료하지 못했습니다.";
}

function mapImpact(impact: DocumentImpactCandidateResponse): Impact {
  return {
    id: impact.id,
    type: "영향 후보",
    depth: null,
    sourceDocument: impact.source_document_id,
    sourceLocation: impact.source_location,
    targetDocument: impact.target_document_id,
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

export function ImpactWorkspace() {
  const [impacts, setImpacts] = useState<Impact[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [documentId, setDocumentId] = useState("");
  const [loadedDocumentId, setLoadedDocumentId] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<RelationshipType | "전체">(
    "전체",
  );
  const [statusFilter, setStatusFilter] = useState<"전체" | Impact["status"]>(
    "전체",
  );
  const [depthFilter, setDepthFilter] = useState<"전체" | Depth>("전체");
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showingFixture, setShowingFixture] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestVersion = useRef(0);

  const loadImpacts = useCallback(
    async (nextDocumentId: string, preferredId?: string) => {
      const requestId = ++requestVersion.current;
      if (!uuidPattern.test(nextDocumentId)) {
        setImpacts([]);
        setSelectedId(null);
        setLoadedDocumentId(null);
        setShowingFixture(false);
        setLoading(false);
        setError("문서 ID는 UUID 형식이어야 합니다.");
        return;
      }

      setLoading(true);
      setShowingFixture(false);
      setError(null);
      try {
        const response = await impactsApi.listDocumentImpactCandidates({
          documentId: nextDocumentId,
        });
        if (requestVersion.current !== requestId) return;
        const mappedImpacts = (response.data.impacts ?? []).map(mapImpact);
        setImpacts(mappedImpacts);
        setLoadedDocumentId(nextDocumentId);
        setSelectedId(
          mappedImpacts.some((impact) => impact.id === preferredId)
            ? (preferredId ?? null)
            : (mappedImpacts[0]?.id ?? null),
        );
      } catch (requestError) {
        if (requestVersion.current !== requestId) return;
        setImpacts([]);
        setSelectedId(null);
        setLoadedDocumentId(null);
        setError(
          `ImpactsApi 조회에 실패했습니다: ${errorMessage(requestError)}`,
        );
      } finally {
        if (requestVersion.current === requestId) setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    const urlDocumentId = new URLSearchParams(window.location.search).get(
      "documentId",
    );
    if (!urlDocumentId) return;
    const normalizedDocumentId = urlDocumentId.trim();
    setDocumentId(normalizedDocumentId);
    void loadImpacts(normalizedDocumentId);
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

  function submitDocumentId(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedDocumentId = documentId.trim();
    setDocumentId(normalizedDocumentId);
    void loadImpacts(normalizedDocumentId);
  }

  function showFixture() {
    requestVersion.current += 1;
    setLoading(false);
    setError(null);
    setShowingFixture(true);
    setImpacts(fixtureImpacts);
    setSelectedId(fixtureImpacts[0].id);
  }

  async function performAction(
    action: "confirm" | "reject" | "required" | "not-required",
  ) {
    if (!selectedImpact || showingFixture) return;
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

      if (!loadedDocumentId) return;
      await loadImpacts(loadedDocumentId, selectedImpact.id);
    } catch (requestError) {
      setError(`ImpactsApi 조치에 실패했습니다: ${errorMessage(requestError)}`);
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <div className={styles.workspace}>
      <aside className={styles.filters} aria-label="관계 필터">
        <div className={styles.panelHeading}>
          <div>
            <p className={styles.eyebrow}>변경 전파 검토</p>
            <h1>관계·영향</h1>
          </div>
          {showingFixture && (
            <span className={styles.fixtureBadge}>Fixture</span>
          )}
        </div>
        <p className={styles.fixtureNote}>
          UUID 문서 ID를 입력하면 실제 영향 후보를 조회합니다. 예시 데이터는
          아래 &apos;시안 보기&apos;를 선택한 경우에만 표시됩니다.
        </p>
        <form onSubmit={submitDocumentId}>
          <label>
            문서 UUID
            <input
              aria-describedby="document-id-help"
              onChange={(event) => setDocumentId(event.target.value)}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={documentId}
            />
          </label>
          <p id="document-id-help">URL의 documentId도 자동으로 조회합니다.</p>
          <button type="submit">영향 후보 조회</button>
          <button onClick={showFixture} type="button">
            시안 보기
          </button>
        </form>
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

      <section className={styles.mainPanel} aria-labelledby="relation-heading">
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

        {showingFixture ? (
          <figure className={styles.map} aria-labelledby="map-caption">
            <svg aria-hidden="true" viewBox="0 0 620 180" role="img">
              <path
                className={styles.svgCandidate}
                d="M135 50 C220 50 240 50 310 50"
              />
              <path
                className={styles.svgConfirmed}
                d="M310 50 C390 50 405 105 485 105"
              />
              <path
                className={styles.svgCandidate}
                d="M135 135 C230 135 350 135 485 105"
              />
              <circle className={styles.svgNode} cx="110" cy="50" r="25" />
              <circle className={styles.svgNode} cx="110" cy="135" r="25" />
              <circle className={styles.svgNode} cx="335" cy="50" r="25" />
              <circle className={styles.svgNode} cx="510" cy="105" r="25" />
              <text x="77" y="55">
                SRS
              </text>
              <text x="78" y="140">
                VAL
              </text>
              <text x="305" y="55">
                DS
              </text>
              <text x="478" y="110">
                QA
              </text>
            </svg>
            <figcaption id="map-caption">
              시안 관계 맵입니다. 실선은 확정, 점선은 검토가 필요한 후보를
              뜻합니다.
            </figcaption>
          </figure>
        ) : (
          <p className={styles.empty}>
            실제 API 응답에는 관계 맵 좌표가 없어 후보 목록으로 표시합니다.
          </p>
        )}

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
                  impact.id === selectedImpact?.id ? styles.selected : undefined
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
                : loadedDocumentId
                  ? "선택한 필터에 맞는 관계가 없습니다."
                  : "문서 UUID를 입력해 영향 후보를 조회하세요."}
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
          <p className={styles.statusText}>
            조회할 문서 UUID를 입력하거나 시안을 선택하세요.
          </p>
        )}
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        {selectedImpact && (
          <fieldset aria-label="관계 검토 조치" className={styles.actions}>
            <button
              disabled={
                showingFixture ||
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
                showingFixture ||
                pendingAction !== null ||
                selectedImpact.status !== CandidateStatus.Candidate
              }
              onClick={() => performAction("reject")}
              type="button"
            >
              {pendingAction === "reject" ? "반려 중…" : "후보 반려"}
            </button>
            <button
              disabled={showingFixture || pendingAction !== null}
              onClick={() => performAction("required")}
              type="button"
            >
              {pendingAction === "required" ? "저장 중…" : "수정 필요"}
            </button>
            <button
              disabled={showingFixture || pendingAction !== null}
              onClick={() => performAction("not-required")}
              type="button"
            >
              {pendingAction === "not-required" ? "저장 중…" : "수정 불필요"}
            </button>
          </fieldset>
        )}
        <p className={styles.actionHint}>
          {showingFixture
            ? "시안 데이터에서는 조치를 실행할 수 없습니다."
            : "자동 확정하지 않습니다. 각 조치 성공 후 목록을 다시 조회합니다."}
        </p>
      </aside>
    </div>
  );
}
