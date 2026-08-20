"use client";

import { useEffect, useState } from "react";

import { documentsApi } from "@/api/client";
import {
  CompileStatus,
  ConversionDecision,
  ConversionStatus,
} from "@/api/generated";
import {
  useLatexPreview,
  useLatexProject,
  useReviewLatexConversionMutation,
} from "@/features/document-workbench/use-latex-project";

import styles from "./conversion-review.module.css";

function requestStatus(error: unknown) {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "status" in error.response &&
    typeof error.response.status === "number"
  ) {
    return error.response.status;
  }

  return null;
}

function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "변환 검토 요청을 완료하지 못했습니다.";
}

function conversionStatusLabel(status: ConversionStatus) {
  if (status === ConversionStatus.Accepted) return "수락됨";
  if (status === ConversionStatus.Rejected) return "반려됨";
  if (status === ConversionStatus.PendingReview) return "사람 검토 대기";
  return "검토 대상 아님";
}

export function ConversionReview({ documentId }: { documentId: string }) {
  const project = useLatexProject(documentId);
  const currentProject = project.data;
  const preview = useLatexPreview(
    documentId,
    currentProject?.revision_id,
    currentProject?.preview_available ?? false,
    currentProject?.compile_status,
  );
  const review = useReviewLatexConversionMutation(documentId);
  const [reason, setReason] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [downloadingOriginal, setDownloadingOriginal] = useState(false);

  useEffect(() => {
    if (!preview.data) {
      setPreviewUrl(null);
      return;
    }

    const url = URL.createObjectURL(preview.data);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [preview.data]);

  async function submit(decision: ConversionDecision) {
    if (!currentProject || !reason.trim()) return;

    setFeedback(null);
    try {
      await review.mutateAsync({
        expected_revision_id: currentProject.revision_id,
        decision,
        reason: reason.trim(),
      });
      setFeedback(
        decision === ConversionDecision.Accepted
          ? "변환을 수락했습니다."
          : "변환을 반려했습니다.",
      );
    } catch (error) {
      if (requestStatus(error) === 409) {
        setFeedback(
          "다른 변경으로 검토 기준 리비전이 갱신되었습니다. 최신 리비전을 다시 불러왔습니다. 작성한 사유를 확인한 뒤 다시 결정하세요.",
        );
        await project.refetch();
        return;
      }

      setFeedback(errorMessage(error));
    }
  }

  async function downloadOriginal() {
    setDownloadingOriginal(true);
    setFeedback(null);
    try {
      const response = await documentsApi.downloadOriginalDocument(
        { documentId },
        { responseType: "blob" },
      );
      const data: unknown = response.data;
      const blob = data instanceof Blob ? data : new Blob([data as BlobPart]);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `original-${documentId}.docx`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setFeedback(`원본 DOCX 다운로드에 실패했습니다: ${errorMessage(error)}`);
    } finally {
      setDownloadingOriginal(false);
    }
  }

  if (project.isPending) {
    return (
      <output className={styles.loading} aria-live="polite">
        LaTeX 프로젝트와 컴파일 미리보기를 확인하는 중입니다.
      </output>
    );
  }

  if (project.isError || !currentProject) {
    return (
      <section className={styles.error} aria-live="assertive">
        <h1>변환 검토 정보를 불러올 수 없습니다</h1>
        <p>
          {project.error ? errorMessage(project.error) : "프로젝트가 없습니다."}
        </p>
        <button onClick={() => void project.refetch()} type="button">
          다시 불러오기
        </button>
      </section>
    );
  }

  const compileSucceeded =
    currentProject.compile_status === CompileStatus.Succeeded;
  const pendingReview =
    currentProject.conversion_status === ConversionStatus.PendingReview;
  const terminalDecision =
    currentProject.conversion_status === ConversionStatus.Accepted ||
    currentProject.conversion_status === ConversionStatus.Rejected;
  const decisionDisabled =
    review.isPending ||
    !reason.trim() ||
    !compileSucceeded ||
    preview.isPending ||
    preview.isError ||
    !previewUrl;

  return (
    <div className={styles.workspace}>
      <section
        className={styles.intro}
        aria-labelledby="conversion-review-heading"
      >
        <div>
          <p className={styles.eyebrow}>DOCX 가져오기 검토</p>
          <h1 id="conversion-review-heading">
            LaTeX 변환 후보를 사람 검토로 확정
          </h1>
          <p>
            DOCX는 불변의 가져오기 입력입니다. 원본 DOCX, 생성된 LaTeX 리비전과
            그 리비전에서 컴파일한 PDF를 대조해 검토합니다.
          </p>
        </div>
        <p className={styles.status}>
          결정 상태:{" "}
          <strong>
            {conversionStatusLabel(currentProject.conversion_status)}
          </strong>
        </p>
      </section>

      <section className={styles.notice} aria-labelledby="limitation-heading">
        <h2 id="limitation-heading">자동 변환의 한계</h2>
        <p>
          자동 변환 결과는 검토 후보일 뿐입니다. Pandoc 변환만으로 원본 DOCX의
          시각적 충실도가 입증되지는 않으며, 원본을 다운로드해 LaTeX 소스와
          컴파일 PDF를 대조한 뒤 사유를 남겨 결정해야 합니다.
        </p>
        <button
          className={styles.originalDownload}
          disabled={downloadingOriginal}
          onClick={downloadOriginal}
          type="button"
        >
          {downloadingOriginal ? "원본 준비 중" : "불변 원본 DOCX 다운로드"}
        </button>
      </section>

      <section className={styles.metadata} aria-labelledby="revision-heading">
        <div>
          <p className={styles.sectionLabel}>불변 가져오기 맥락</p>
          <h2 id="revision-heading">DOCX 가져오기에서 생성된 리비전</h2>
          <dl>
            <div>
              <dt>원본</dt>
              <dd>불변 DOCX 가져오기 입력</dd>
            </div>
            <div>
              <dt>리비전 출처</dt>
              <dd>{currentProject.origin}</dd>
            </div>
            <div>
              <dt>리비전 ID</dt>
              <dd>{currentProject.revision_id}</dd>
            </div>
            <div>
              <dt>소스 SHA-256</dt>
              <dd>{currentProject.source_sha256}</dd>
            </div>
            <div>
              <dt>컴파일 PDF SHA-256</dt>
              <dd>
                {currentProject.compiled_pdf_sha256 ?? "컴파일 산출물 없음"}
              </dd>
            </div>
            <div>
              <dt>진입점</dt>
              <dd>{currentProject.entrypoint}</dd>
            </div>
          </dl>
        </div>
        <div>
          <p className={styles.sectionLabel}>프로젝트 번들</p>
          <h2>리비전에 포함된 파일</h2>
          <ul className={styles.fileList}>
            {currentProject.files.map((file) => (
              <li key={file}>{file}</li>
            ))}
          </ul>
        </div>
      </section>

      <section
        className={styles.previewGrid}
        aria-label="LaTeX 소스와 컴파일 PDF"
      >
        <div className={styles.sourcePanel}>
          <p className={styles.sectionLabel}>진입점 소스</p>
          <h2>{currentProject.entrypoint}</h2>
          <pre>
            <code>{currentProject.source}</code>
          </pre>
        </div>
        <div className={styles.pdfPanel}>
          <p className={styles.sectionLabel}>정확한 파생 미리보기</p>
          <h2>이 리비전에서 컴파일한 PDF</h2>
          {!compileSucceeded && (
            <p className={styles.compileBlocked} role="alert">
              컴파일이 성공하지 않아 변환 검토를 진행할 수 없습니다.
              {currentProject.compile_log
                ? ` 컴파일 로그: ${currentProject.compile_log}`
                : ""}
            </p>
          )}
          {compileSucceeded && preview.isPending && (
            <output aria-live="polite">컴파일 PDF를 불러오는 중입니다.</output>
          )}
          {compileSucceeded && preview.isError && (
            <p className={styles.compileBlocked} role="alert">
              컴파일 PDF를 불러오지 못했습니다. 검토 결정을 내릴 수 없습니다.
            </p>
          )}
          {compileSucceeded && previewUrl && !preview.isError && (
            <iframe
              className={styles.pdfPreview}
              src={previewUrl}
              title="현재 LaTeX 리비전에서 컴파일한 PDF 미리보기"
            />
          )}
        </div>
      </section>

      {pendingReview && (
        <section
          className={styles.decisionPanel}
          aria-labelledby="decision-heading"
        >
          <div>
            <p className={styles.sectionLabel}>사람 결정</p>
            <h2 id="decision-heading">변환 후보 검토 사유</h2>
            <p>
              이 리비전 ID를 기준으로 수락 또는 반려합니다. 사유는 감사 이력에
              남습니다.
            </p>
          </div>
          <label htmlFor="conversion-reason">
            검토 사유 <span aria-hidden="true">*</span>
          </label>
          <textarea
            aria-describedby="conversion-reason-help"
            disabled={review.isPending || !compileSucceeded || preview.isError}
            id="conversion-reason"
            onChange={(event) => setReason(event.target.value)}
            required
            value={reason}
          />
          <p id="conversion-reason-help">
            비어 있지 않은 구체적인 검토 사유를 입력하세요.
          </p>
          <div className={styles.actions}>
            <button
              disabled={decisionDisabled || preview.isError}
              onClick={() => void submit(ConversionDecision.Accepted)}
              type="button"
            >
              {review.isPending ? "결정 기록 중" : "변환 수락"}
            </button>
            <button
              className={styles.reject}
              disabled={decisionDisabled || preview.isError}
              onClick={() => void submit(ConversionDecision.Rejected)}
              type="button"
            >
              반려
            </button>
          </div>
        </section>
      )}

      {terminalDecision && (
        <section className={styles.terminal} aria-live="polite">
          <p className={styles.sectionLabel}>최종 결정</p>
          <h2>
            변환이 {conversionStatusLabel(currentProject.conversion_status)}{" "}
            상태입니다
          </h2>
          <p>이 리비전에 대한 추가 결정은 제공되지 않습니다.</p>
        </section>
      )}

      {feedback && (
        <p className={styles.feedback} aria-live="polite">
          {feedback}
        </p>
      )}
    </div>
  );
}
