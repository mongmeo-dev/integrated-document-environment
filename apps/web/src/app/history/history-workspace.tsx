"use client";

import { useEffect, useMemo, useState } from "react";

import { historyApi } from "@/api/client";
import type { HistoryEvent } from "@/api/generated";

import styles from "./history.module.css";

const historyEventKinds = {
  change_request: "변경 요청 등록",
  change_proposal_decision: "수정안 결정",
  change_comment_status: "변경 의견 상태",
  document_relationship_decision: "문서 관계 결정",
  document_impact_decision: "영향 후보 결정",
  document_impact_modification_decision: "수정 필요 결정",
  evidence_decision: "근거 후보 결정",
  evidence_stale: "근거 재검토 필요",
  evidence_review: "근거 최신성 검토",
  approval_audit: "승인 흐름 변경",
  format_check: "서식 검사 시작",
  format_check_completed: "자동 서식 검사",
  visual_review: "시각 비교 검토",
  document_completion: "최종 완료",
} as const;

type HistoryFilter = keyof typeof historyEventKinds;
type EventKind = (typeof historyEventKinds)[HistoryFilter] | string;

type AuditEvent = {
  id: string;
  kind: EventKind;
  type: string;
  actor: string;
  changedAt: string;
  reason: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  document: string;
};

function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "통합 이력을 불러오지 못했습니다.";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function shortDocumentId(value: string) {
  return value.length > 12 ? `문서 ${value.slice(0, 8)}` : value;
}

function historyToEvent(event: HistoryEvent): AuditEvent {
  return {
    id: `${event.type}-${event.id}`,
    kind: historyEventKinds[event.type as HistoryFilter] ?? event.type,
    type: event.type,
    actor: event.actor_id ? `사용자 ${event.actor_id.slice(0, 8)}` : "시스템",
    changedAt: event.occurred_at,
    reason: event.reason ?? "사유 없음",
    before: event.before,
    after: event.after,
    document: event.document_id,
  };
}

export function HistoryWorkspace({ documentId }: { documentId?: string }) {
  const [historyEvents, setHistoryEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kindFilter, setKindFilter] = useState<"전체" | HistoryFilter>("전체");
  const [documentFilter, setDocumentFilter] = useState("전체");

  useEffect(() => {
    let active = true;

    async function loadHistoryEvents() {
      setLoading(true);
      setError(null);
      try {
        const response = await historyApi.listHistoryEvents({
          documentId:
            documentId ??
            (documentFilter === "전체" ? undefined : documentFilter),
          filter: kindFilter === "전체" ? undefined : kindFilter,
          limit: 100,
        });
        if (active) setHistoryEvents(response.data.map(historyToEvent));
      } catch (requestError) {
        if (active) {
          setHistoryEvents([]);
          setError(
            `감사 이력을 불러오지 못했습니다: ${errorMessage(requestError)}`,
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadHistoryEvents();
    return () => {
      active = false;
    };
  }, [documentFilter, documentId, kindFilter]);

  const events = useMemo(
    () =>
      [...historyEvents].sort(
        (left, right) =>
          new Date(right.changedAt).getTime() -
          new Date(left.changedAt).getTime(),
      ),
    [historyEvents],
  );
  const documents = useMemo(
    () => [...new Set(events.map((event) => event.document))],
    [events],
  );
  const visibleEvents = events.filter(
    (event) =>
      (kindFilter === "전체" || event.type === kindFilter) &&
      (documentId !== undefined ||
        documentFilter === "전체" ||
        event.document === documentFilter),
  );

  return (
    <section className={styles.workspace} id="history-workspace">
      <header className={styles.intro}>
        <div>
          <p className={styles.eyebrow}>영구 변경 이력</p>
          <h1>{documentId ? "문서 감사 이력" : "전체 감사 이력"}</h1>
          <p>
            변경 요청부터 최종 완료까지 결정의 주체, 사유와 전후 값을 시간순으로
            확인합니다.
          </p>
        </div>
      </header>

      <form className={styles.filters} aria-label="감사 이력 필터">
        <label>
          이벤트
          <select
            value={kindFilter}
            onChange={(event) =>
              setKindFilter(event.target.value as "전체" | HistoryFilter)
            }
          >
            <option value="전체">전체 이벤트</option>
            {Object.entries(historyEventKinds).map(([filter, kind]) => (
              <option key={filter} value={filter}>
                {kind}
              </option>
            ))}
          </select>
        </label>
        {!documentId && (
          <label>
            문서
            <select
              value={documentFilter}
              onChange={(event) => setDocumentFilter(event.target.value)}
            >
              <option value="전체">전체 문서</option>
              {documents.map((document) => (
                <option key={document} value={document}>
                  {shortDocumentId(document)}
                </option>
              ))}
            </select>
          </label>
        )}
        <output aria-live="polite">{visibleEvents.length}건 표시</output>
      </form>

      {loading && (
        <output className={styles.loading} aria-live="polite">
          감사 이력을 불러오는 중입니다.
        </output>
      )}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      {visibleEvents.length === 0 ? (
        <output className={styles.empty}>
          선택한 필터에 맞는 감사 이력이 없습니다.
        </output>
      ) : (
        <ol className={styles.timeline} aria-label="시간순 감사 이력">
          {visibleEvents.map((event) => (
            <li key={event.id}>
              <article className={styles.event}>
                <div className={styles.eventMeta}>
                  <span className={styles.kind}>{event.kind}</span>
                  <time dateTime={event.changedAt}>
                    {formatDate(event.changedAt)}
                  </time>
                </div>
                <h2>{event.kind} 기록</h2>
                <p className={styles.eventDocument}>
                  {shortDocumentId(event.document)}
                </p>
                <dl className={styles.summaryFields}>
                  <div>
                    <dt>수행자</dt>
                    <dd>{event.actor}</dd>
                  </div>
                  <div className={styles.reason}>
                    <dt>사유</dt>
                    <dd>{event.reason}</dd>
                  </div>
                </dl>
                <details className={styles.rawDetails}>
                  <summary>변경 전후 원본 보기</summary>
                  <dl className={styles.auditFields}>
                    <div>
                      <dt>변경 전</dt>
                      <dd>
                        <pre>{JSON.stringify(event.before, null, 2)}</pre>
                      </dd>
                    </div>
                    <div>
                      <dt>변경 후</dt>
                      <dd>
                        <pre>{JSON.stringify(event.after, null, 2)}</pre>
                      </dd>
                    </div>
                  </dl>
                </details>
              </article>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
