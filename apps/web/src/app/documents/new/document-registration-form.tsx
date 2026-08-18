"use client";

import { useRef, useState } from "react";

import { documentsApi } from "@/api/client";

import styles from "./new-document.module.css";

type SelectedDocument = {
  name: string;
  size: number;
  type: "DOCX" | "PDF";
  file: File;
};

const docxMimeTypes = [
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/msword",
];
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
  const isDocx =
    extension === "docx" &&
    (file.type === "" || docxMimeTypes.includes(file.type));
  const isPdf =
    extension === "pdf" && (file.type === "" || file.type === pdfMimeType);

  if (!isDocx && !isPdf) {
    return "DOCX 또는 PDF 파일만 선택할 수 있습니다.";
  }

  return {
    name: file.name,
    size: file.size,
    type: isDocx ? "DOCX" : "PDF",
    file,
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
      return;
    }
    setSelectedDocument(result);
    setError("");
  };

  const removeFile = () => {
    setSelectedDocument(undefined);
    setError("");
    setStatus("파일을 선택한 뒤 원본을 등록할 수 있습니다.");
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <form
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
          setStatus("원본 등록을 접수했습니다. 입력 검증으로 이동합니다.");
          const search = new URLSearchParams({ documentId: response.data.id });
          window.location.assign(`/documents/validation/?${search.toString()}`);
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
        <p>DOCX 또는 PDF를 선택하세요. 파일은 이 브라우저에서만 검토합니다.</p>
        <input
          accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.pdf,application/pdf"
          aria-describedby="file-boundary file-error"
          className={styles.fileInput}
          id="document-file"
          onChange={(event) => selectFile(event.target.files?.[0])}
          ref={inputRef}
          type="file"
        />
        <label className={styles.filePicker} htmlFor="document-file">
          <span aria-hidden="true">↑</span>
          <strong>파일 선택</strong>
          <small>DOCX 또는 PDF</small>
        </label>
        <p className={styles.fileBoundary} id="file-boundary">
          지원 형식: DOCX, PDF · 스캔 PDF는 분석 전용
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
      <p className={styles.registrationStatus} id="registration-status">
        {status}
      </p>
    </form>
  );
}
