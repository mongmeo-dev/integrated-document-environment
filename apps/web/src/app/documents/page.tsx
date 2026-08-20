"use client";

import { useEffect, useState } from "react";

import { documentsApi } from "@/api/client";
import {
  type DocumentResponse,
  DocumentStatus,
  InputKind,
} from "@/api/generated";
import { WorkspaceHeader } from "@/components/workspace-header";

import styles from "./documents.module.css";

type DocumentState = "검토 중" | "변경 있음" | "최신";

const filters: Array<DocumentState | "전체"> = [
  "전체",
  "검토 중",
  "변경 있음",
  "최신",
];

const documentStatusByFilter: Partial<Record<DocumentState, DocumentStatus>> = {
  "검토 중": DocumentStatus.Validating,
  "변경 있음": DocumentStatus.Queued,
  최신: DocumentStatus.Ready,
};

const documentStateLabels: Record<DocumentStatus, DocumentState> = {
  [DocumentStatus.Queued]: "변경 있음",
  [DocumentStatus.Validating]: "검토 중",
  [DocumentStatus.Ready]: "최신",
  [DocumentStatus.Rejected]: "검토 중",
};

const inputKindLabels = {
  [InputKind.LatexProject]: "LaTeX 프로젝트 · 정본",
  [InputKind.DocxImport]: "DOCX 가져오기 · 변환 검토",
  [InputKind.TextPdf]: "텍스트 PDF · 참조",
  [InputKind.ScannedPdf]: "스캔 PDF · 분석 전용",
} as const;

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function apiErrorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "문서 목록을 불러오지 못했습니다.";
}

export default function DocumentsPage() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [filter, setFilter] = useState<(typeof filters)[number]>("전체");
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initialQuery = new URLSearchParams(window.location.search)
      .get("query")
      ?.trim();
    if (initialQuery) {
      setQuery(initialQuery);
      setDebouncedQuery(initialQuery);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedQuery(query);
    }, 250);

    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    let active = true;

    async function loadDocuments() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await documentsApi.listDocuments({
          query: debouncedQuery.trim() || undefined,
          status:
            filter === "전체" ? undefined : documentStatusByFilter[filter],
        });
        if (active) setDocuments(response.data);
      } catch (requestError) {
        if (active) setError(apiErrorMessage(requestError));
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void loadDocuments();
    return () => {
      active = false;
    };
  }, [debouncedQuery, filter]);

  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#document-list">
        문서 목록으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/documents/" />

      <div className={styles.workspace}>
        <section className={styles.content} id="document-list">
          <div className={styles.titleRow}>
            <div>
              <h1>문서 탐색</h1>
              <p>등록된 원본 문서의 상태와 검토 작업을 한곳에서 확인합니다.</p>
            </div>
            <a className={styles.newDocument} href="/documents/new/">
              <span aria-hidden="true">+</span> 문서 등록 준비
            </a>
          </div>

          <div className={styles.controls}>
            <label className={styles.search}>
              <span aria-hidden="true">⌕</span>
              <span className={styles.visuallyHidden}>문서 검색</span>
              <input
                onChange={(event) => setQuery(event.target.value)}
                placeholder="파일명으로 검색"
                type="search"
                value={query}
              />
            </label>
            <fieldset className={styles.filters}>
              <legend className={styles.visuallyHidden}>상태 필터</legend>
              {filters.map((item) => (
                <button
                  aria-pressed={filter === item}
                  className={filter === item ? styles.activeFilter : undefined}
                  key={item}
                  onClick={() => setFilter(item)}
                  type="button"
                >
                  {item}
                </button>
              ))}
            </fieldset>
          </div>

          <div className={styles.listSummary}>
            <span aria-live="polite">
              {isLoading ? "문서 검색 중" : `검색 결과 ${documents.length}개`}
            </span>
            <span>등록 시각 기준</span>
          </div>
          {isLoading ? (
            <p className={styles.empty} aria-live="polite">
              문서 목록을 불러오는 중입니다.
            </p>
          ) : error ? (
            <p className={styles.empty} role="alert">
              문서 목록을 불러오지 못했습니다: {error}
            </p>
          ) : documents.length === 0 ? (
            <p className={styles.empty}>
              검색 또는 상태 조건에 맞는 문서가 없습니다.
            </p>
          ) : (
            <ul className={styles.documentList}>
              <li aria-hidden="true" className={styles.columnHeaders}>
                <span>문서</span>
                <span>형식</span>
                <span>입력 유형</span>
                <span>현재 상태</span>
                <span>등록 시각</span>
                <span />
              </li>
              {documents.map((document) => {
                const type =
                  document.input_kind === InputKind.LatexProject
                    ? "LaTeX"
                    : document.input_kind === InputKind.DocxImport
                      ? "DOCX 가져오기"
                      : "PDF 참조";
                const state = documentStateLabels[document.status];
                const inputKind = document.input_kind
                  ? inputKindLabels[document.input_kind]
                  : "입력 유형 확인 중";
                return (
                  <li className={styles.documentRow} key={document.id}>
                    <div className={styles.documentName}>
                      <a
                        href={`/documents/${document.id}/`}
                        className={styles.documentLink}
                      >
                        {document.original_file.original_filename}
                      </a>
                      <span className={styles.documentId}>
                        ID {document.id.slice(0, 8)}
                      </span>
                    </div>
                    <span className={styles.fileType} data-label="형식">
                      <span
                        className={
                          type === "LaTeX"
                            ? styles.latexType
                            : type === "DOCX 가져오기"
                              ? styles.wordType
                              : styles.pdfType
                        }
                        aria-hidden="true"
                      >
                        {type === "LaTeX"
                          ? "TeX"
                          : type === "DOCX 가져오기"
                            ? "W"
                            : "PDF"}
                      </span>
                      {type}
                    </span>
                    <span className={styles.inputKind} data-label="입력 유형">
                      {inputKind}
                    </span>
                    <span
                      className={`${styles.state} ${state === "변경 있음" ? styles.changed : state === "검토 중" ? styles.review : styles.current}`}
                      data-label="현재 상태"
                    >
                      {state}
                    </span>
                    <span className={styles.updated} data-label="등록 시각">
                      {formatDate(document.created_at)}
                    </span>
                    <a
                      aria-label={`${document.original_file.original_filename} 열기`}
                      className={styles.openDocument}
                      href={`/documents/${document.id}/`}
                    >
                      열기 <span aria-hidden="true">›</span>
                    </a>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
