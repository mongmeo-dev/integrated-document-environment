"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { documentsApi } from "@/api/client";
import { DocumentStatus } from "@/api/generated";

import styles from "./document-workspace-shell.module.css";
import { WorkspaceHeader } from "./workspace-header";

type DocumentSection =
  | "overview"
  | "validation"
  | "workbench"
  | "import-review"
  | "changes"
  | "impact"
  | "evidence"
  | "approvals"
  | "completion"
  | "history";

const sections: Array<{
  id: Exclude<DocumentSection, "history">;
  label: string;
}> = [
  { id: "overview", label: "개요" },
  { id: "validation", label: "원본 검증" },
  { id: "workbench", label: "LaTeX 작업대" },
  { id: "import-review", label: "변환 검토" },
  { id: "changes", label: "변경 검토" },
  { id: "impact", label: "영향" },
  { id: "evidence", label: "근거" },
  { id: "approvals", label: "승인" },
  { id: "completion", label: "완료" },
];

const statusLabels: Record<DocumentStatus, string> = {
  [DocumentStatus.Queued]: "검증 대기",
  [DocumentStatus.Validating]: "검증 중",
  [DocumentStatus.Ready]: "작업 가능",
  [DocumentStatus.Rejected]: "입력 차단",
};

function sectionHref(documentId: string, section: DocumentSection) {
  if (section === "overview") return `/documents/${documentId}/`;
  return `/documents/${documentId}/${section}/`;
}

export function DocumentWorkspaceShell({
  children,
  currentSection,
  documentId,
}: {
  children: React.ReactNode;
  currentSection: DocumentSection;
  documentId: string;
}) {
  const { data: document } = useQuery({
    queryKey: ["document", documentId],
    queryFn: async () => (await documentsApi.getDocument({ documentId })).data,
  });

  const title = document?.original_file.original_filename ?? "문서 작업공간";
  const mediaType = document?.original_file.media_type ?? "";
  const filename =
    document?.original_file.original_filename.toLowerCase() ?? "";
  const format =
    mediaType === "text/x-tex" ||
    mediaType === "application/x-tex" ||
    mediaType === "text/plain" ||
    filename.endsWith(".tex")
      ? "LaTeX 원본"
      : mediaType === "application/zip" || filename.endsWith(".zip")
        ? "LaTeX 프로젝트"
        : mediaType.includes("word") || filename.endsWith(".docx")
          ? "DOCX 가져오기"
          : mediaType.includes("pdf") || filename.endsWith(".pdf")
            ? "PDF 참조"
            : "형식 확인 중";

  return (
    <div className={styles.shell}>
      <a className={styles.skipLink} href="#document-workspace-content">
        현재 작업으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/documents/" />
      <header className={styles.documentHeader}>
        <div className={styles.documentIdentity}>
          <Link href="/documents/">문서</Link>
          <span aria-hidden="true">/</span>
          <div>
            <strong>{title}</strong>
            <span>
              {format} ·{" "}
              {document ? statusLabels[document.status] : "문서 정보 확인 중"}
            </span>
          </div>
        </div>
        <nav aria-label="문서 작업 단계" className={styles.stageNav}>
          {sections
            .filter(
              (section) =>
                (section.id !== "workbench" ||
                  document?.capabilities.source_editing) &&
                (section.id !== "import-review" ||
                  document?.capabilities.conversion_review),
            )
            .map((section) => (
              <Link
                aria-current={
                  currentSection === section.id ? "page" : undefined
                }
                href={sectionHref(documentId, section.id)}
                key={section.id}
              >
                {section.label}
              </Link>
            ))}
        </nav>
        <Link
          className={styles.historyLink}
          aria-current={currentSection === "history" ? "page" : undefined}
          href={sectionHref(documentId, "history")}
        >
          문서 이력
        </Link>
      </header>
      <main className={styles.content} id="document-workspace-content">
        {children}
      </main>
    </div>
  );
}
