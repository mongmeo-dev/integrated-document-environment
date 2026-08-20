"use client";

import { useEffect, useMemo, useState } from "react";

import { documentsApi } from "@/api/client";
import { type DocumentResponse, DocumentStatus } from "@/api/generated";
import { WorkspaceHeader } from "@/components/workspace-header";

import styles from "./page.module.css";

type WorkFilter = "all" | "review" | "available" | "blocked";

type WorkState = {
  label: string;
  filter: Exclude<WorkFilter, "all">;
};

const workStates: Record<DocumentStatus, WorkState> = {
  [DocumentStatus.Validating]: { label: "검토 필요", filter: "review" },
  [DocumentStatus.Ready]: { label: "진행 가능", filter: "available" },
  [DocumentStatus.Queued]: { label: "입력 차단", filter: "blocked" },
  [DocumentStatus.Rejected]: { label: "입력 차단", filter: "blocked" },
};

const filterLabels: Record<WorkFilter, string> = {
  all: "전체 작업",
  review: "검토 필요",
  available: "진행 가능",
  blocked: "입력 차단",
};

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "등록 시각 확인 중";

  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function documentFormat(document: DocumentResponse) {
  return document.original_file.media_type.toLowerCase().includes("pdf")
    ? "PDF"
    : "DOCX";
}

function abbreviatedId(id: string) {
  return id.length > 12 ? `${id.slice(0, 8)}…${id.slice(-4)}` : id;
}

function apiErrorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "문서 목록을 불러오지 못했습니다.";
}

export default function Home() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [filter, setFilter] = useState<WorkFilter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadDocuments() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await documentsApi.listDocuments();
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
  }, []);

  const documentCounts = useMemo(
    () =>
      documents.reduce<Record<Exclude<WorkFilter, "all">, number>>(
        (counts, document) => {
          counts[workStates[document.status].filter] += 1;
          return counts;
        },
        { review: 0, available: 0, blocked: 0 },
      ),
    [documents],
  );

  const visibleDocuments = useMemo(
    () =>
      filter === "all"
        ? documents
        : documents.filter(
            (document) => workStates[document.status].filter === filter,
          ),
    [documents, filter],
  );

  return (
    <div className={styles.app}>
      <a className={styles.skipLink} href="#work-queue">
        내 작업 목록으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/" />

      <main className={styles.workspace} id="work-queue">
        <header className={styles.pageHeader}>
          <div>
            <p className={styles.eyebrow}>문서 작업공간</p>
            <h1>내 작업</h1>
            <p className={styles.introduction}>
              등록된 문서의 현재 상태를 확인하고 필요한 작업을 이어갑니다.
            </p>
          </div>
          <a className={styles.registerLink} href="/documents/new/">
            문서 등록
          </a>
        </header>

        <section aria-label="문서 작업 상태" className={styles.filters}>
          {(Object.keys(filterLabels) as WorkFilter[]).map((item) => {
            const count =
              item === "all" ? documents.length : documentCounts[item];
            return (
              <button
                aria-pressed={filter === item}
                className={filter === item ? styles.activeFilter : undefined}
                key={item}
                onClick={() => setFilter(item)}
                type="button"
              >
                <span>{filterLabels[item]}</span>
                <strong>{count}</strong>
              </button>
            );
          })}
        </section>

        <section aria-labelledby="queue-heading" className={styles.queue}>
          <div className={styles.queueHeader}>
            <div>
              <p className={styles.eyebrow}>작업 큐</p>
              <h2 id="queue-heading">{filterLabels[filter]}</h2>
            </div>
            {!isLoading && !error ? (
              <p className={styles.documentCount}>
                문서 {visibleDocuments.length}개
              </p>
            ) : null}
          </div>

          {isLoading ? (
            <p aria-live="polite" className={styles.stateMessage}>
              내 작업 목록을 불러오는 중입니다.
            </p>
          ) : error ? (
            <div className={styles.errorMessage} role="alert">
              <strong>내 작업 목록을 불러오지 못했습니다.</strong>
              <p>{error}</p>
            </div>
          ) : visibleDocuments.length === 0 ? (
            <p className={styles.stateMessage}>
              {filter === "all"
                ? "현재 등록된 문서가 없습니다. 문서를 등록하여 작업을 시작하세요."
                : `${filterLabels[filter]} 상태의 문서가 없습니다.`}
            </p>
          ) : (
            <ul className={styles.documentList}>
              {visibleDocuments.map((document) => {
                const format = documentFormat(document);
                const state = workStates[document.status];
                return (
                  <li key={document.id}>
                    <a
                      className={styles.documentRow}
                      href={`/documents/${encodeURIComponent(document.id)}/`}
                    >
                      <span
                        aria-hidden="true"
                        className={`${styles.fileType} ${format === "PDF" ? styles.pdf : styles.docx}`}
                      >
                        {format === "PDF" ? "PDF" : "W"}
                      </span>
                      <span className={styles.documentDetails}>
                        <strong>
                          {document.original_file.original_filename}
                        </strong>
                        <span className={styles.metadata}>
                          <span
                            className={styles.documentId}
                            title={document.id}
                          >
                            ID {abbreviatedId(document.id)}
                          </span>
                          <span>{format}</span>
                          <span>등록 {formatDate(document.created_at)}</span>
                        </span>
                      </span>
                      <span
                        className={`${styles.status} ${styles[state.filter]}`}
                      >
                        <span aria-hidden="true" className={styles.statusDot} />
                        {state.label}
                      </span>
                      <span aria-hidden="true" className={styles.chevron}>
                        ›
                      </span>
                    </a>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
