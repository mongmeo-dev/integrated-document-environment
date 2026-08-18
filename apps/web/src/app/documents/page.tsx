"use client";

import { useEffect, useState } from "react";

import { documentsApi } from "@/api/client";
import { type DocumentResponse, DocumentStatus } from "@/api/generated";
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
  const [filter, setFilter] = useState<(typeof filters)[number]>("전체");
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initialQuery = new URLSearchParams(window.location.search)
      .get("query")
      ?.trim();
    if (initialQuery) setQuery(initialQuery);
  }, []);

  useEffect(() => {
    let active = true;

    async function loadDocuments() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await documentsApi.listDocuments({
          query: query.trim() || undefined,
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
  }, [filter, query]);

  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#document-list">
        문서 목록으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/documents/" />

      <div className={styles.workspace}>
        <aside className={styles.sidebar} aria-label="문서 작업공간">
          <p className={styles.eyebrow}>현재 작업공간</p>
          <strong>SaMD Core v2.4</strong>
          <div className={styles.branch}>문서 등록 및 검토</div>
          <nav aria-label="문서 범주" className={styles.tree}>
            <strong>문서 구조</strong>
            <a aria-current="page" href="/documents">
              전체 문서 <b>{documents.length}</b>
            </a>
            <a href="/documents/validation">원본 입력 검증 상태</a>
          </nav>
          <section className={styles.sidebarNote}>
            <span>등록 범위</span>
            <p>DOCX 및 PDF 원본을 등록 준비할 수 있습니다.</p>
          </section>
        </aside>

        <section className={styles.content} id="document-list">
          <div className={styles.breadcrumb}>문서 구조 / 전체 문서</div>
          <div className={styles.titleRow}>
            <div>
              <h1>문서 탐색</h1>
              <p>변경 상태와 검토 맥락을 기준으로 작업 문서를 찾습니다.</p>
            </div>
            <a className={styles.newDocument} href="/documents/new">
              <span aria-hidden="true">+</span> 문서 등록 준비
            </a>
          </div>

          <div className={styles.controls}>
            <label className={styles.search}>
              <span aria-hidden="true">⌕</span>
              <span className={styles.visuallyHidden}>문서 검색</span>
              <input
                onChange={(event) => setQuery(event.target.value)}
                placeholder="문서명 또는 문서 ID 검색"
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
            <span>표시 문서 {documents.length}개</span>
            <span>최근 등록 순</span>
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
              {documents.map((document) => {
                const type = document.original_file.media_type.includes("pdf")
                  ? "PDF"
                  : "DOCX";
                const state = documentStateLabels[document.status];
                return (
                  <li className={styles.documentRow} key={document.id}>
                    <span
                      className={
                        type === "DOCX" ? styles.wordType : styles.pdfType
                      }
                    >
                      {type === "DOCX" ? "W" : "PDF"}
                    </span>
                    <div className={styles.documentName}>
                      <strong>
                        {document.original_file.original_filename}
                      </strong>
                      <span>
                        {document.id} ·{" "}
                        {document.input_kind ?? "입력 유형 확인 중"}
                      </span>
                    </div>
                    <span
                      className={`${styles.state} ${state === "변경 있음" ? styles.changed : state === "검토 중" ? styles.review : styles.current}`}
                    >
                      {state}
                    </span>
                    <span className={styles.updated}>
                      {formatDate(document.created_at)}
                    </span>
                    <a
                      aria-label={`${document.original_file.original_filename} 변경 요청 열기`}
                      className={styles.openDocument}
                      href={`/documents/nd-srs-002/changes/?documentId=${encodeURIComponent(document.id)}`}
                    >
                      열기 <span aria-hidden="true">›</span>
                    </a>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <aside className={styles.activity} aria-label="문서 등록 안내">
          <div className={styles.activityHeading}>
            <span>문서 작업</span>
            <h2>등록 및 검토</h2>
          </div>
          <section className={styles.formatSupport}>
            <span>지원 형식</span>
            <strong>DOCX · PDF</strong>
            <p>등록한 원본의 검증 상태와 변경 요청을 문서별로 확인합니다.</p>
          </section>
        </aside>
      </div>
    </main>
  );
}
