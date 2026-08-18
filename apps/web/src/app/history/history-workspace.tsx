"use client";

import { useEffect, useMemo, useState } from "react";

import { historyApi } from "@/api/client";
import type { HistoryEvent } from "@/api/generated";

import styles from "./history.module.css";

const historyEventKinds = {
  change_request: "변경 요청",
  change_proposal_decision: "수정안 결정",
  change_comment_status: "변경 요청",
  document_relationship_decision: "관계·영향 결정",
  document_impact_decision: "관계·영향 결정",
  document_impact_modification_decision: "관계·영향 결정",
  evidence_decision: "근거 stale/review",
  evidence_stale: "근거 stale/review",
  evidence_review: "근거 stale/review",
  approval_audit: "승인 단계·흐름 변경",
  format_check: "서식 검증",
  format_check_completed: "서식 검증",
  visual_review: "서식 검증",
  document_completion: "최종 완료",
} as const;

type HistoryFilter = keyof typeof historyEventKinds;
type EventKind = (typeof historyEventKinds)[HistoryFilter] | string;

type AuditEvent = {
  id: string;
  kind: EventKind;
  actor: string;
  changedAt: string;
  reason: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  document: string;
  source: "Fixture" | "HistoryApi";
};

const fixtureEvents: AuditEvent[] = [
  {
    id: "fixture-change-001",
    kind: "변경 요청",
    actor: "KM · 문서 소유자",
    changedAt: "2026-08-18T09:40:00Z",
    reason:
      "세션 만료 요구사항의 재인증 조건을 명확히 하기 위해 변경을 요청했습니다.",
    before: { section: "§ 4.2", reauthentication: "명시되지 않음" },
    after: { section: "§ 4.2", reauthentication: "30분 비활성 후 필수" },
    document: "ND-SRS-002 · 사용자 접근 통제",
    source: "Fixture",
  },
  {
    id: "fixture-revision-001",
    kind: "수정안 결정",
    actor: "JH · 요구사항 검토자",
    changedAt: "2026-08-18T09:25:00Z",
    reason: "검증 가능한 조건과 용어가 포함된 수정안을 채택했습니다.",
    before: { proposal: "재인증 안내 추가", decision: "검토 중" },
    after: { proposal: "30분 비활성 후 재인증", decision: "채택" },
    document: "ND-SRS-002 · 사용자 접근 통제",
    source: "Fixture",
  },
  {
    id: "fixture-impact-001",
    kind: "관계·영향 결정",
    actor: "MS · 출시 책임자",
    changedAt: "2026-08-18T09:10:00Z",
    reason:
      "세션 정책 변경이 TC-12와 인증 서비스에 영향을 준다고 확정했습니다.",
    before: { relations: [], impact: "미평가" },
    after: {
      relations: ["ND-VAL-008 · TC-12", "services/auth/session.py"],
      impact: "영향 있음",
    },
    document: "ND-SRS-002 · 사용자 접근 통제",
    source: "Fixture",
  },
  {
    id: "fixture-evidence-stale-001",
    kind: "근거 stale/review",
    actor: "KM · 품질 보증",
    changedAt: "2026-08-18T08:56:00Z",
    reason:
      "요구사항 변경으로 기존 서버 코드 근거의 최신성을 다시 검토해야 합니다.",
    before: { evidence: "services/auth/session.py", freshness: "현재" },
    after: { evidence: "services/auth/session.py", freshness: "오래됨" },
    document: "ND-SRS-002 · 사용자 접근 통제",
    source: "Fixture",
  },
  {
    id: "fixture-evidence-review-001",
    kind: "근거 stale/review",
    actor: "JH · 요구사항 검토자",
    changedAt: "2026-08-18T08:50:00Z",
    reason:
      "TC-12 실행 결과가 수정된 조건을 충족하는지 검토하여 현재로 확인했습니다.",
    before: { evidence: "VAL-008 / TC-12", freshness: "오래됨" },
    after: { evidence: "VAL-008 / TC-12", freshness: "현재" },
    document: "ND-VAL-008 · 접근 통제 검증",
    source: "Fixture",
  },
  {
    id: "fixture-approval-001",
    kind: "승인 단계·흐름 변경",
    actor: "KM · 품질 보증",
    changedAt: "2026-08-18T08:30:00Z",
    reason: "요구사항 검토 완료 후 품질 보증 승인 단계로 진행했습니다.",
    before: { step: 1, status: "현재", nextStep: "요구사항 검토" },
    after: { step: 2, status: "현재", nextStep: "품질 보증 승인" },
    document: "ND-SRS-002 · 사용자 접근 통제",
    source: "Fixture",
  },
  {
    id: "fixture-format-001",
    kind: "서식 검증",
    actor: "CI · 서식 검증",
    changedAt: "2026-08-18T08:20:00Z",
    reason: "필수 제목 계층과 표 열 구성을 검사하여 서식 검증을 통과했습니다.",
    before: { validation: "실행 전", violations: null },
    after: { validation: "통과", violations: 0 },
    document: "ND-SRS-002 · 사용자 접근 통제",
    source: "Fixture",
  },
  {
    id: "fixture-completion-001",
    kind: "최종 완료",
    actor: "MS · 출시 책임자",
    changedAt: "2026-08-18T08:05:00Z",
    reason:
      "필수 검토, 승인, 서식 검증 결과를 확인하고 변경 요청을 완료했습니다.",
    before: { status: "승인 대기", completion: false },
    after: { status: "완료", completion: true },
    document: "ND-CHG-018 · 세션 정책 변경",
    source: "Fixture",
  },
];

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

function historyToEvent(event: HistoryEvent): AuditEvent {
  return {
    id: `history-api-${event.type}-${event.id}`,
    kind: historyEventKinds[event.type as HistoryFilter] ?? event.type,
    actor: event.actor_id ?? "알 수 없음",
    changedAt: event.occurred_at,
    reason: event.reason ?? "사유 없음",
    before: event.before,
    after: event.after,
    document: event.document_id,
    source: "HistoryApi",
  };
}

export function HistoryWorkspace() {
  const [historyEvents, setHistoryEvents] = useState<AuditEvent[]>([]);
  const [useFixtureFallback, setUseFixtureFallback] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kindFilter, setKindFilter] = useState<"전체" | HistoryFilter>("전체");
  const [documentFilter, setDocumentFilter] = useState("전체");

  useEffect(() => {
    let active = true;

    async function loadHistoryEvents() {
      setLoading(true);
      setError(null);
      setUseFixtureFallback(false);
      try {
        const response = await historyApi.listHistoryEvents({
          documentId: documentFilter === "전체" ? undefined : documentFilter,
          filter: kindFilter === "전체" ? undefined : kindFilter,
          limit: 100,
        });
        if (active) setHistoryEvents(response.data.map(historyToEvent));
      } catch (requestError) {
        if (active) {
          setHistoryEvents([]);
          setUseFixtureFallback(true);
          setError(
            `HistoryApi 통합 이력 조회가 실패했습니다. 시안 Fixture를 표시합니다: ${errorMessage(requestError)}`,
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
  }, [documentFilter, kindFilter]);

  const events = useMemo(
    () =>
      [...(useFixtureFallback ? fixtureEvents : historyEvents)].sort(
        (left, right) =>
          new Date(right.changedAt).getTime() -
          new Date(left.changedAt).getTime(),
      ),
    [historyEvents, useFixtureFallback],
  );
  const documents = useMemo(
    () => [...new Set(events.map((event) => event.document))],
    [events],
  );
  const visibleEvents = events.filter(
    (event) =>
      (kindFilter === "전체" || event.kind === historyEventKinds[kindFilter]) &&
      (documentFilter === "전체" || event.document === documentFilter),
  );

  return (
    <section className={styles.workspace} id="history-workspace">
      <header className={styles.intro}>
        <div>
          <p className={styles.eyebrow}>영구 변경 이력</p>
          <h1>감사 이력</h1>
          <p>
            변경 요청부터 최종 완료까지 결정의 주체, 사유와 전후 값을 시간순으로
            확인합니다.
          </p>
        </div>
        {useFixtureFallback && (
          <aside className={styles.fixtureNotice} aria-label="데이터 범위">
            <strong>시안 Fixture 표시 중</strong>
            <p>
              통합 history API를 불러오지 못해 예시 데이터를 표시합니다. 실제
              영속 이력이 아닙니다.
            </p>
          </aside>
        )}
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
        <label>
          문서
          <select
            value={documentFilter}
            onChange={(event) => setDocumentFilter(event.target.value)}
          >
            <option value="전체">전체 문서</option>
            {documents.map((document) => (
              <option key={document} value={document}>
                {document}
              </option>
            ))}
          </select>
        </label>
        <output aria-live="polite">{visibleEvents.length}건 표시</output>
      </form>

      {loading && (
        <output className={styles.loading} aria-live="polite">
          HistoryApi 통합 이력을 조회하는 중입니다.
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
                  <span
                    className={
                      event.source === "Fixture"
                        ? styles.fixtureBadge
                        : styles.apiBadge
                    }
                  >
                    {event.source === "Fixture" ? "Fixture" : "HistoryApi"}
                  </span>
                  <time dateTime={event.changedAt}>
                    {formatDate(event.changedAt)}
                  </time>
                </div>
                <h2>{event.document}</h2>
                <dl className={styles.auditFields}>
                  <div>
                    <dt>Actor</dt>
                    <dd>{event.actor}</dd>
                  </div>
                  <div className={styles.reason}>
                    <dt>Reason</dt>
                    <dd>{event.reason}</dd>
                  </div>
                  <div>
                    <dt>Before</dt>
                    <dd>
                      <pre>{JSON.stringify(event.before, null, 2)}</pre>
                    </dd>
                  </div>
                  <div>
                    <dt>After</dt>
                    <dd>
                      <pre>{JSON.stringify(event.after, null, 2)}</pre>
                    </dd>
                  </div>
                </dl>
              </article>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
