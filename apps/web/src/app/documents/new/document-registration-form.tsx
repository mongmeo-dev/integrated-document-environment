"use client";

import { useRef, useState } from "react";

import { documentsApi } from "@/api/client";

import styles from "./new-document.module.css";

type SelectedDocument = {
  name: string;
  size: number;
  type: "LaTeX 원본" | "LaTeX 프로젝트" | "DOCX 가져오기" | "PDF 참조";
  authority: string;
  file: File;
};

const docxMimeTypes = [
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const texMimeTypes = ["text/x-tex", "application/x-tex", "text/plain"];
const zipMimeType = "application/zip";
const pdfMimeType = "application/pdf";

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function validateFile(file: File): SelectedDocument | string {
  if (file.size === 0) {
    return "빈 파일은 등록 준비에 사용할 수 없습니다.";
  }

  const extension = file.name.split(".").pop()?.toLowerCase();
  const isTex =
    extension === "tex" &&
    (file.type === "" || texMimeTypes.includes(file.type));
  const isZip =
    extension === "zip" && (file.type === "" || file.type === zipMimeType);
  const isDocx =
    extension === "docx" &&
    (file.type === "" || docxMimeTypes.includes(file.type));
  const isPdf =
    extension === "pdf" && (file.type === "" || file.type === pdfMimeType);

  if (!isTex && !isZip && !isDocx && !isPdf) {
    return ".tex, .zip, DOCX 또는 PDF 파일만 선택할 수 있습니다.";
  }

  return {
    name: file.name,
    size: file.size,
    type: isTex
      ? "LaTeX 원본"
      : isZip
        ? "LaTeX 프로젝트"
        : isDocx
          ? "DOCX 가져오기"
          : "PDF 참조",
    authority:
      isTex || isZip
        ? "정본 LaTeX 원본"
        : isDocx
          ? "일방향 변환 입력 · 사람 검토 필요"
          : "참조·분석 전용",
    file:
      file.type === ""
        ? new File([file], file.name, {
            type: isTex
              ? "text/x-tex"
              : isZip
                ? zipMimeType
                : isDocx
                  ? docxMimeTypes[0]
                  : pdfMimeType,
          })
        : file,
  };
}

export default function DocumentRegistrationForm() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedDocument, setSelectedDocument] = useState<SelectedDocument>();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState(
    "파일을 선택한 뒤 원본을 등록할 수 있습니다.",
  );

  const selectFile = (file: File | undefined) => {
    if (!file) return;
    const result = validateFile(file);
    if (typeof result === "string") {
      setSelectedDocument(undefined);
      setError(result);
      setStatus("파일을 다시 선택하세요.");
      if (inputRef.current) inputRef.current.value = "";
      return;
    }
    setSelectedDocument(result);
    setError("");
    setStatus(
      result.type === "DOCX 가져오기"
        ? "DOCX는 자동 변환 후 사람이 변환 결과를 검토해야 합니다."
        : result.type === "PDF 참조"
          ? "PDF는 참조·분석 전용으로 등록할 수 있습니다."
          : "LaTeX 정본을 등록하고 작업대에서 편집·컴파일할 수 있습니다.",
    );
  };

  const removeFile = () => {
    setSelectedDocument(undefined);
    setError("");
    setStatus("파일을 선택한 뒤 원본을 등록할 수 있습니다.");
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <form
      aria-busy={isSubmitting}
      className={styles.form}
      onSubmit={async (event) => {
        event.preventDefault();
        if (!selectedDocument || isSubmitting) return;
        setIsSubmitting(true);
        setError("");
        setStatus("원본 파일을 등록하고 있습니다.");
        try {
          const response = await documentsApi.registerDocument({
            file: selectedDocument.file,
          });
          setStatus("원본 등록이 완료되었습니다. 자동 검증으로 이동합니다.");
          window.location.assign(`/documents/${response.data.id}/validation/`);
        } catch {
          setError("등록하지 못했습니다. 로그인 상태와 API 연결을 확인하세요.");
          setStatus("원본 등록에 실패했습니다.");
        } finally {
          setIsSubmitting(false);
        }
      }}
    >
      <fieldset>
        <legend>원본 파일 선택</legend>
        <p>
          LaTeX 프로젝트를 정본으로 등록하세요. DOCX와 PDF는 보조 입력으로만
          사용합니다.
        </p>
        <input
          accept=".tex,text/x-tex,application/x-tex,text/plain,.zip,application/zip,.docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.pdf,application/pdf"
          aria-describedby={
            error ? "file-boundary file-error" : "file-boundary"
          }
          aria-invalid={Boolean(error)}
          className={styles.fileInput}
          id="document-file"
          onChange={(event) => selectFile(event.target.files?.[0])}
          ref={inputRef}
          type="file"
        />
        <label className={styles.filePicker} htmlFor="document-file">
          <span aria-hidden="true" className={styles.uploadIcon}>
            ↑
          </span>
          <strong>LaTeX 원본 또는 프로젝트 선택</strong>
          <small>.tex 또는 .zip 권장 · DOCX 가져오기 · PDF 참조</small>
        </label>
        <p className={styles.fileBoundary} id="file-boundary">
          <strong>LaTeX(.tex/.zip)</strong>는 편집·컴파일의 정본입니다.{" "}
          <strong>DOCX</strong>는 LaTeX로 자동 일방향 변환되며, 변환 결과는
          사람이 사유와 함께 검토·확정해야 합니다. <strong>PDF</strong>는
          참조·분석 전용입니다.
        </p>
        {error && (
          <p
            aria-live="polite"
            className={styles.error}
            id="file-error"
            role="alert"
          >
            {error}
          </p>
        )}
      </fieldset>

      {selectedDocument ? (
        <section aria-labelledby="review-title" className={styles.fileReview}>
          <div className={styles.reviewHeading}>
            <div>
              <span>등록 전 검토</span>
              <h2 id="review-title">선택한 원본</h2>
            </div>
            <button
              className={styles.removeButton}
              onClick={removeFile}
              type="button"
            >
              제거
            </button>
          </div>
          <dl>
            <div>
              <dt>이름</dt>
              <dd>{selectedDocument.name}</dd>
            </div>
            <div>
              <dt>크기</dt>
              <dd>{formatFileSize(selectedDocument.size)}</dd>
            </div>
            <div>
              <dt>유형</dt>
              <dd>
                <span className={styles.fileType}>{selectedDocument.type}</span>
                <span className={styles.authority}>
                  {selectedDocument.authority}
                </span>
              </dd>
            </div>
          </dl>
          <output className={styles.apiNotice}>
            <strong>원본 보존</strong> 등록 시 원본은 변경하지 않고 별도
            보관됩니다.
          </output>
        </section>
      ) : (
        <section className={styles.reviewEmpty} aria-live="polite">
          파일을 선택하면 이름, 크기, 유형을 등록 전에 검토할 수 있습니다.
        </section>
      )}

      <div className={styles.actions}>
        <a className={styles.cancelButton} href="/documents">
          취소
        </a>
        <button
          aria-describedby="registration-status"
          className={styles.registerButton}
          disabled={!selectedDocument || isSubmitting}
          type="submit"
        >
          {isSubmitting ? "등록 중" : "등록"}
        </button>
      </div>
      <p
        aria-live="polite"
        className={styles.registrationStatus}
        id="registration-status"
      >
        {status}
      </p>
    </form>
  );
}
