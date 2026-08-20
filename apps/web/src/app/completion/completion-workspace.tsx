"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { completionApi, latexApi } from "@/api/client";
import {
  CompletionBlockingCode,
  type CompletionBlockingReason,
  type CompletionEvaluation,
  type DocumentCompletionResponse,
  type LatexProjectResponse,
} from "@/api/generated";

import styles from "./completion.module.css";

type Gate = {
  id: string;
  label: string;
  detail: string;
  codes: CompletionBlockingCode[];
  path:
    | "changes"
    | "impact"
    | "evidence"
    | "workbench"
    | "import-review"
    | "approvals";
};

const gates: Gate[] = [
  {
    id: "canonical-source",
    label: "LaTeX 정본",
    detail: "최신 LaTeX 리비전을 완료 대상으로 고정해야 합니다.",
    codes: [
      CompletionBlockingCode.LatexProjectMissing,
      CompletionBlockingCode.LatexRevisionNotFound,
      CompletionBlockingCode.LatexRevisionDocumentMismatch,
      CompletionBlockingCode.LatexRevisionNotLatest,
    ],
    path: "workbench",
  },
  {
    id: "compilation",
    label: "컴파일 PDF",
    detail: "최신 정본의 컴파일이 성공하고 PDF가 존재해야 합니다.",
    codes: [
      CompletionBlockingCode.CompileIncomplete,
      CompletionBlockingCode.CompileFailed,
      CompletionBlockingCode.CompiledPdfMissing,
    ],
    path: "workbench",
  },
  {
    id: "conversion-review",
    label: "DOCX 변환 검토",
    detail: "DOCX 변환 후보는 사유가 있는 사람 결정으로 확정해야 합니다.",
    codes: [
      CompletionBlockingCode.ConversionReviewPending,
      CompletionBlockingCode.ConversionRejected,
    ],
    path: "import-review",
  },
  {
    id: "changes",
    label: "변경",
    detail: "열린 변경 요청과 수정안을 모두 결정합니다.",
    codes: [
      CompletionBlockingCode.PendingChangeRequests,
      CompletionBlockingCode.PendingChangeProposals,
    ],
    path: "changes",
  },
  {
    id: "relationships",
    label: "관계",
    detail: "관계 후보를 확정 또는 제외합니다.",
    codes: [CompletionBlockingCode.PendingRelationshipCandidates],
    path: "impact",
  },
  {
    id: "impacts",
    label: "영향",
    detail: "영향 후보와 필요한 수정 결정을 닫습니다.",
    codes: [CompletionBlockingCode.PendingImpactCandidates],
    path: "impact",
  },
  {
    id: "evidence",
    label: "근거",
    detail: "근거 후보와 오래된 근거를 모두 검토합니다.",
    codes: [
      CompletionBlockingCode.PendingEvidenceCandidates,
      CompletionBlockingCode.StaleEvidence,
    ],
    path: "evidence",
  },
  {
    id: "approvals",
    label: "승인 단계",
    detail: "순차 승인 단계가 모두 완료되어야 합니다.",
    codes: [
      CompletionBlockingCode.ApprovalWorkflowMissing,
      CompletionBlockingCode.ApprovalStepsIncomplete,
    ],
    path: "approvals",
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

export function CompletionWorkspace({ documentId }: { documentId: string }) {
  const [project, setProject] = useState<LatexProjectResponse | null>(null);
  const [evaluation, setEvaluation] = useState<CompletionEvaluation | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState<
    "evaluate" | "complete" | "export" | null
  >(null);
  const [error, setError] = useState<string | null>(null);
  const [empty, setEmpty] = useState<string | null>(null);
  const [completion, setCompletion] =
    useState<DocumentCompletionResponse | null>(null);

  const evaluate = useCallback(async () => {
    setAction("evaluate");
    setLoading(true);
    setError(null);
    setEmpty(null);
    try {
      const projectResponse = await latexApi.getLatexProject({ documentId });
      setProject(projectResponse.data);
      const response = await completionApi.evaluateDocumentCompletion({
        completionRequest: {
          document_id: documentId,
          latex_revision_id: projectResponse.data.revision_id,
        },
      });
      setEvaluation(response.data);
    } catch (requestError) {
      setProject(null);
      setEvaluation(null);
      setEmpty(
        "완료 대상으로 평가할 LaTeX 정본이 없습니다. 원본 검증과 작업대 컴파일을 먼저 완료하세요.",
      );
      setError(`완료 조건 평가가 실패했습니다: ${errorMessage(requestError)}`);
    } finally {
      setLoading(false);
      setAction(null);
    }
  }, [documentId]);

  useEffect(() => {
    void evaluate();
  }, [evaluate]);

  const reasons = evaluation?.blocking_reasons ?? [];
  const alreadyCompleted = reasons.some(
    (reason) => reason.code === CompletionBlockingCode.DocumentAlreadyCompleted,
  );
  const activeReasons = reasons.filter(
    (reason) => reason.code !== CompletionBlockingCode.DocumentAlreadyCompleted,
  );
  const totalBlockers = activeReasons.reduce(
    (total, reason) => total + reason.count,
    0,
  );
  const isBlocked = totalBlockers > 0 || alreadyCompleted;
  const gateStates = useMemo(
    () =>
      gates.map((gate) => ({
        gate,
        count: countFor(gate, activeReasons),
      })),
    [activeReasons],
  );

  if (!evaluation || !project) {
    return (
      <div className={styles.workspace} id="completion-workspace">
        <header className={styles.intro} aria-busy={loading}>
          <h1>최종 완료 판단</h1>
          {loading && (
            <output className={styles.loading}>
              LaTeX 정본과 완료 조건을 평가 중입니다.
            </output>
          )}
          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}
          {!loading && (
            <div>
              <p>{empty ?? "완료 조건을 평가할 정본을 찾지 못했습니다."}</p>
              <a href={`/documents/${documentId}/workbench/`}>
                LaTeX 작업대 열기
              </a>
            </div>
          )}
        </header>
      </div>
    );
  }

  const activeEvaluation = evaluation;

  async function complete() {
    if (isBlocked || completion) return;
    setAction("complete");
    setError(null);
    try {
      const response = await completionApi.completeDocument({
        completionRequest: {
          document_id: activeEvaluation.document_id,
          latex_revision_id: activeEvaluation.latex_revision_id,
        },
      });
      setCompletion(response.data);
      await evaluate();
    } catch (requestError) {
      setError(`최종 완료 요청이 실패했습니다: ${errorMessage(requestError)}`);
    } finally {
      setAction(null);
    }
  }

  async function downloadExport() {
    if (!completion && !alreadyCompleted) return;
    setAction("export");
    setError(null);
    try {
      const response = await completionApi.downloadApprovalExport(
        { documentId },
        { responseType: "blob" },
      );
      const blob =
        response.data instanceof Blob
          ? response.data
          : new Blob([response.data]);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${documentId}_승인완료.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(
        `승인 PDF 다운로드 요청이 실패했습니다: ${errorMessage(requestError)}`,
      );
    } finally {
      setAction(null);
    }
  }

  return (
    <div className={styles.workspace} id="completion-workspace">
      <header className={styles.intro}>
        <div>
          <p className={styles.eyebrow}>최종 완료 게이트</p>
          <h1>최종 완료 판단</h1>
          <p>
            최신 LaTeX 정본과 그 정본에서 컴파일한 PDF를 고정한 뒤 모든 게이트를
            평가합니다.
          </p>
        </div>
        <div className={styles.outputFormat}>
          <span>승인 산출 형식</span>
          <strong>컴파일 PDF</strong>
          <small title={project.compiled_pdf_sha256 ?? undefined}>
            정본 {project.revision_id.slice(0, 8)} · PDF 해시{" "}
            {project.compiled_pdf_sha256?.slice(0, 12) ?? "없음"}
          </small>
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
          <p className={styles.eyebrow}>정본·산출 경계</p>
          <h2 id="boundary-heading">
            최신 LaTeX 리비전과 정확한 PDF만 산출합니다
          </h2>
        </div>
        <p>
          DOCX 원본, PDF 참조 입력 또는 과거 컴파일 결과는 승인 산출로 사용할 수
          없습니다. 현재 완료 대상은{" "}
          <code>{activeEvaluation.latex_revision_id}</code>입니다.
        </p>
      </section>

      <section aria-labelledby="gates-heading">
        <div className={styles.sectionHeading}>
          <div>
            <p className={styles.eyebrow}>완료 전 검사</p>
            <h2 id="gates-heading">완료 게이트</h2>
          </div>
          <strong
            className={
              totalBlockers > 0 ? styles.blockedCount : styles.clearCount
            }
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
              {count > 0 && (
                <a href={`/documents/${documentId}/${gate.path}/`}>
                  해결 화면으로 이동
                </a>
              )}
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
            모든 게이트가 통과한 뒤 담당자가 최종 완료를 실행하며, 완료 기록은
            정확한 LaTeX 리비전과 컴파일 PDF 해시에 고정됩니다.
          </p>
        </div>
        <div className={styles.actions}>
          <button disabled={action !== null} onClick={evaluate} type="button">
            {action === "evaluate" ? "재평가 중" : "완료 조건 재평가"}
          </button>
          <button
            disabled={isBlocked || action !== null || completion !== null}
            onClick={complete}
            type="button"
          >
            {action === "complete"
              ? "최종 완료 처리 중"
              : alreadyCompleted
                ? "완료됨"
                : "사람의 최종 책임으로 완료"}
          </button>
        </div>
      </section>

      {(completion || alreadyCompleted) && (
        <section className={styles.completed} aria-live="polite">
          <div>
            <p className={styles.eyebrow}>최종 완료</p>
            <h2>문서 완료가 기록되었습니다</h2>
            <p>
              {completion
                ? `${completion.completed_by_id} · ${new Intl.DateTimeFormat(
                    "ko-KR",
                    {
                      dateStyle: "medium",
                      timeStyle: "short",
                    },
                  ).format(new Date(completion.completed_at))}`
                : "저장된 완료 기록의 컴파일 PDF를 다운로드할 수 있습니다."}
            </p>
          </div>
          <button
            disabled={action !== null}
            onClick={downloadExport}
            type="button"
          >
            {action === "export" ? "다운로드 준비 중" : "승인 PDF 다운로드"}
          </button>
        </section>
      )}
    </div>
  );
}
