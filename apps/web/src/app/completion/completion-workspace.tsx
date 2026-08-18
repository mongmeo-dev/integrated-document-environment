"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { completionApi } from "@/api/client";
import {
  CompletionBlockingCode,
  type CompletionBlockingReason,
  type CompletionEvaluation,
  type DocumentCompletionResponse,
} from "@/api/generated";

import styles from "./completion.module.css";

const fixtureEvaluation: CompletionEvaluation = {
  document_id: "ND-SRS-002",
  external_edit_result_id: "fixture-external-result-002",
  blocking_reasons: [
    { code: CompletionBlockingCode.PendingChangeRequests, count: 1 },
    { code: CompletionBlockingCode.PendingChangeProposals, count: 2 },
    { code: CompletionBlockingCode.PendingRelationshipCandidates, count: 1 },
    { code: CompletionBlockingCode.PendingImpactCandidates, count: 1 },
    { code: CompletionBlockingCode.PendingEvidenceCandidates, count: 2 },
    { code: CompletionBlockingCode.StaleEvidence, count: 1 },
    { code: CompletionBlockingCode.VisualReviewIncomplete, count: 1 },
    { code: CompletionBlockingCode.UnresolvedFormatDifferences, count: 5 },
    { code: CompletionBlockingCode.ApprovalStepsIncomplete, count: 2 },
  ],
};

type Gate = {
  id: string;
  label: string;
  detail: string;
  codes: CompletionBlockingCode[];
};

const gates: Gate[] = [
  {
    id: "changes",
    label: "변경",
    detail: "열린 변경 요청과 수정안을 모두 결정합니다.",
    codes: [
      CompletionBlockingCode.PendingChangeRequests,
      CompletionBlockingCode.PendingChangeProposals,
    ],
  },
  {
    id: "relationships",
    label: "관계",
    detail: "관계 후보를 확정 또는 제외합니다.",
    codes: [CompletionBlockingCode.PendingRelationshipCandidates],
  },
  {
    id: "impacts",
    label: "영향",
    detail: "영향 후보와 필요한 수정 결정을 닫습니다.",
    codes: [CompletionBlockingCode.PendingImpactCandidates],
  },
  {
    id: "evidence",
    label: "근거",
    detail: "근거 후보를 검토하고 연결 상태를 확정합니다.",
    codes: [CompletionBlockingCode.PendingEvidenceCandidates],
  },
  {
    id: "freshness",
    label: "오래됨",
    detail: "오래된 근거를 갱신하거나 검토합니다.",
    codes: [CompletionBlockingCode.StaleEvidence],
  },
  {
    id: "automatic-format",
    label: "자동 서식",
    detail: "동일 형식 산출의 자동 서식 검사를 통과해야 합니다.",
    codes: [
      CompletionBlockingCode.FormatResultNotPassed,
      CompletionBlockingCode.AutomaticCheckIncomplete,
    ],
  },
  {
    id: "visual-comparison",
    label: "시각 비교",
    detail: "사람이 원본과 산출을 시각적으로 검토해야 합니다.",
    codes: [CompletionBlockingCode.VisualReviewIncomplete],
  },
  {
    id: "differences",
    label: "미해결 차이",
    detail: "서식 비교에서 남은 차이를 모두 해결합니다.",
    codes: [CompletionBlockingCode.UnresolvedFormatDifferences],
  },
  {
    id: "approvals",
    label: "승인 단계",
    detail: "순차 승인 단계가 모두 완료되어야 합니다.",
    codes: [
      CompletionBlockingCode.ApprovalWorkflowMissing,
      CompletionBlockingCode.ApprovalStepsIncomplete,
    ],
  },
];

function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "API 요청을 완료하지 못했습니다.";
}

function countFor(gate: Gate, reasons: CompletionBlockingReason[]) {
  return reasons
    .filter((reason) => gate.codes.includes(reason.code))
    .reduce((total, reason) => total + reason.count, 0);
}

export function CompletionWorkspace() {
  const [searchParams] = useState(
    () =>
      new URLSearchParams(
        typeof window === "undefined" ? "" : window.location.search,
      ),
  );
  const documentId = searchParams.get("documentId");
  const externalResultId = searchParams.get("externalResultId");
  const request =
    documentId && externalResultId
      ? { document_id: documentId, external_edit_result_id: externalResultId }
      : null;
  const [evaluation, setEvaluation] = useState<CompletionEvaluation | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState<
    "evaluate" | "complete" | "export" | null
  >(null);
  const [error, setError] = useState<string | null>(null);
  const [completion, setCompletion] =
    useState<DocumentCompletionResponse | null>(null);
  const [showFixture, setShowFixture] = useState(false);

  const evaluate = useCallback(async () => {
    if (showFixture) {
      setEvaluation(fixtureEvaluation);
      return;
    }
    if (!request) {
      setEvaluation(null);
      return;
    }
    setAction("evaluate");
    setLoading(true);
    setError(null);
    try {
      const response = await completionApi.evaluateDocumentCompletion({
        completionRequest: request,
      });
      setEvaluation(response.data);
    } catch (requestError) {
      setError(`완료 조건 평가가 실패했습니다: ${errorMessage(requestError)}`);
    } finally {
      setLoading(false);
      setAction(null);
    }
  }, [request, showFixture]);

  useEffect(() => {
    void evaluate();
  }, [evaluate]);

  const reasons = evaluation?.blocking_reasons ?? [];
  const totalBlockers = reasons.reduce(
    (total, reason) => total + reason.count,
    0,
  );
  const boundaryBlockers = reasons.filter(
    (reason) =>
      reason.code === CompletionBlockingCode.ScannedPdf ||
      reason.code === CompletionBlockingCode.CrossFormatResult ||
      reason.code === CompletionBlockingCode.UnsupportedOriginalFormat,
  );
  const isBlocked = totalBlockers > 0;
  const gateStates = useMemo(
    () => gates.map((gate) => ({ gate, count: countFor(gate, reasons) })),
    [reasons],
  );

  if (!evaluation) {
    return (
      <div className={styles.workspace} id="completion-workspace">
        <header className={styles.intro} aria-busy={loading}>
          <h1>최종 완료 판단</h1>
          {loading && (
            <output className={styles.loading}>
              완료 조건을 평가 중입니다.
            </output>
          )}
          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}
          {!loading && !error && (
            <>
              <p>
                URL에 documentId와 externalResultId를 지정해 완료 조건을
                평가하세요.
              </p>
              <button onClick={() => setShowFixture(true)} type="button">
                시안 보기
              </button>
            </>
          )}
        </header>
      </div>
    );
  }

  async function complete() {
    if (!request || isBlocked || completion) return;
    setAction("complete");
    setError(null);
    try {
      const response = await completionApi.completeDocument({
        completionRequest: request,
      });
      setCompletion(response.data);
      await evaluate();
    } catch (requestError) {
      setError(
        `CompletionApi 최종 완료 요청이 실패했습니다: ${errorMessage(requestError)}`,
      );
    } finally {
      setAction(null);
    }
  }

  async function downloadExport() {
    if (!completion) return;
    setAction("export");
    setError(null);
    try {
      const response = await completionApi.downloadApprovalExport(
        {
          documentId: completion.document_id,
        },
        { responseType: "blob" },
      );
      const blob =
        response.data instanceof Blob
          ? response.data
          : new Blob([response.data]);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${completion.document_id}_승인완료.${completion.original_format}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(
        `CompletionApi 승인 산출 다운로드 요청이 실패했습니다: ${errorMessage(requestError)}`,
      );
    } finally {
      setAction(null);
    }
  }

  return (
    <div className={styles.workspace} id="completion-workspace">
      <header className={styles.intro}>
        <div>
          <p className={styles.eyebrow}>
            Phase 1 완료 게이트 ·{" "}
            {showFixture && (
              <span className={styles.fixtureBadge}>Fixture</span>
            )}
          </p>
          <h1>{evaluation.document_id} · 최종 완료 판단</h1>
          <p>
            모든 게이트를 통과한 뒤에만 사람의 최종 책임으로 문서를 완료합니다.
          </p>
        </div>
        <div className={styles.outputFormat}>
          <span>승인 산출 형식</span>
          <strong>DOCX · 원본과 동일 형식</strong>
          <small>교차 형식 변환 산출은 완료할 수 없습니다.</small>
        </div>
      </header>

      {loading && (
        <output className={styles.loading}>완료 조건을 평가 중입니다.</output>
      )}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      <section className={styles.boundary} aria-labelledby="boundary-heading">
        <div>
          <p className={styles.eyebrow}>입력·산출 경계</p>
          <h2 id="boundary-heading">스캔 PDF와 교차 형식 산출은 차단됩니다</h2>
        </div>
        <p>
          편집 가능한 원본과 동일한 형식의 외부 편집 결과만 완료 대상으로
          평가합니다.{" "}
          {boundaryBlockers.length > 0
            ? `현재 경계 차단 ${boundaryBlockers.reduce((total, reason) => total + reason.count, 0)}건`
            : "현재 경계 차단 없음"}
        </p>
      </section>

      <section aria-labelledby="gates-heading">
        <div className={styles.sectionHeading}>
          <div>
            <p className={styles.eyebrow}>완료 전 검사</p>
            <h2 id="gates-heading">완료 게이트</h2>
          </div>
          <strong
            className={isBlocked ? styles.blockedCount : styles.clearCount}
          >
            차단 {totalBlockers}건
          </strong>
        </div>
        <ol className={styles.gateList}>
          {gateStates.map(({ gate, count }) => (
            <li
              className={count > 0 ? styles.gateBlocked : styles.gatePassed}
              key={gate.id}
            >
              <div>
                <strong>{gate.label}</strong>
                <p>{gate.detail}</p>
              </div>
              <span>
                <span className={styles.visuallyHidden}>{gate.label} </span>
                {count}건
              </span>
              <b>{count > 0 ? "차단" : "통과"}</b>
            </li>
          ))}
        </ol>
      </section>

      <section
        className={styles.approvalBoundary}
        aria-labelledby="final-heading"
      >
        <div>
          <p className={styles.eyebrow}>승인과 완료의 구분</p>
          <h2 id="final-heading">승인 단계 완료는 최종 완료가 아닙니다</h2>
          <p>
            단계 승인은 하나의 게이트입니다. 모든 게이트가 통과한 뒤 담당자가
            최종 완료를 실행하며, 그 판단과 산출에 대한 최종 책임은 사람에게
            있습니다.
          </p>
        </div>
        <div className={styles.actions}>
          <button disabled={action !== null} onClick={evaluate} type="button">
            {action === "evaluate" ? "재평가 중" : "완료 조건 재평가"}
          </button>
          <button
            disabled={
              !request || isBlocked || action !== null || completion !== null
            }
            onClick={complete}
            type="button"
          >
            {action === "complete"
              ? "최종 완료 처리 중"
              : "사람의 최종 책임으로 완료"}
          </button>
        </div>
      </section>

      {completion && (
        <section className={styles.completed} aria-live="polite">
          <div>
            <p className={styles.eyebrow}>최종 완료</p>
            <h2>문서 완료가 기록되었습니다</h2>
            <p>
              {completion.completed_by_id} ·{" "}
              {new Intl.DateTimeFormat("ko-KR", {
                dateStyle: "medium",
                timeStyle: "short",
              }).format(new Date(completion.completed_at))}
            </p>
          </div>
          <button
            disabled={action !== null}
            onClick={downloadExport}
            type="button"
          >
            {action === "export"
              ? "다운로드 준비 중"
              : `승인 산출 다운로드 · ${completion.original_format.toUpperCase()}`}
          </button>
        </section>
      )}
    </div>
  );
}
