import { cookies } from "next/headers";
import Link from "next/link";

import { documentsApi } from "@/api/client";
import { DocumentStatus, InputKind } from "@/api/generated";
import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";

import styles from "./overview.module.css";

const statusCopy = {
  [DocumentStatus.Queued]: "검증 대기",
  [DocumentStatus.Validating]: "검증 중",
  [DocumentStatus.Ready]: "작업 가능",
  [DocumentStatus.Rejected]: "입력 차단",
} as const;

const inputKindCopy = {
  [InputKind.LatexProject]: "LaTeX 프로젝트 · 정본",
  [InputKind.DocxImport]: "DOCX 가져오기 · 변환 검토 필요",
  [InputKind.TextPdf]: "텍스트 PDF",
  [InputKind.ScannedPdf]: "스캔 PDF · 분석 전용",
} as const;

const capabilityRows = [
  ["analysis", "분석"],
  ["source_editing", "LaTeX 원본 편집"],
  ["compilation", "PDF 컴파일"],
  ["conversion_review", "변환 검토"],
  ["approved_output", "승인 산출물"],
] as const;

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default async function DocumentOverviewPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  try {
    const sessionToken = (await cookies()).get("ide_session")?.value;
    const { data: document } = await documentsApi.getDocument(
      { documentId, ideSession: sessionToken },
      sessionToken
        ? { headers: { Cookie: `ide_session=${sessionToken}` } }
        : undefined,
    );
    const isPdf =
      document.input_kind === InputKind.TextPdf ||
      document.input_kind === InputKind.ScannedPdf;
    const nextStep =
      document.status !== DocumentStatus.Ready
        ? {
            href: `/documents/${documentId}/validation/`,
            label: "원본 검증 확인",
            description:
              "작업을 시작하기 전에 원본 검증 상태와 제한을 확인합니다.",
          }
        : isPdf
          ? {
              href: `/documents/${documentId}/changes/`,
              label: "분석 결과 검토",
              description: "PDF는 참조·분석 범위에서 변경 사항을 검토합니다.",
            }
          : {
              href: `/documents/${documentId}/workbench/`,
              label: "LaTeX 작업대 열기",
              description:
                document.input_kind === InputKind.DocxImport
                  ? "자동 변환된 LaTeX 원본을 확인하고 변환 검토를 진행합니다."
                  : "LaTeX 원본을 편집하고 컴파일 PDF를 확인합니다.",
            };

    return (
      <DocumentWorkspaceShell currentSection="overview" documentId={documentId}>
        <div className={styles.workspace}>
          <header className={styles.heading}>
            <p className={styles.eyebrow}>DOCUMENT OVERVIEW</p>
            <h1>{document.original_file.original_filename}</h1>
            <p>현재 문서의 입력 상태와 사용 가능한 작업 범위를 확인합니다.</p>
          </header>

          <section className={styles.summary} aria-label="문서 상태">
            <div>
              <span>상태</span>
              <strong>{statusCopy[document.status]}</strong>
            </div>
            <div>
              <span>형식</span>
              <strong>
                {document.input_kind === InputKind.LatexProject
                  ? "LaTeX 프로젝트"
                  : document.input_kind === InputKind.DocxImport
                    ? "DOCX 가져오기"
                    : document.input_kind === InputKind.TextPdf ||
                        document.input_kind === InputKind.ScannedPdf
                      ? "PDF 참조"
                      : "형식 확인 중"}
              </strong>
            </div>
            <div>
              <span>입력 유형</span>
              <strong>
                {document.input_kind
                  ? inputKindCopy[document.input_kind]
                  : "판별 중 또는 거부됨"}
              </strong>
            </div>
          </section>

          <div className={styles.detailsGrid}>
            <section
              className={styles.panel}
              aria-labelledby="capabilities-title"
            >
              <h2 id="capabilities-title">사용 가능 범위</h2>
              <dl>
                {capabilityRows.map(([key, label]) => (
                  <div key={key}>
                    <dt>{label}</dt>
                    <dd>
                      {document.capabilities[key] ? "사용 가능" : "사용 불가"}
                    </dd>
                  </div>
                ))}
              </dl>
            </section>
            <section className={styles.panel} aria-labelledby="source-title">
              <h2 id="source-title">원본 정보</h2>
              <dl>
                <div>
                  <dt>파일 크기</dt>
                  <dd>{formatBytes(document.original_file.size_bytes)}</dd>
                </div>
                <div>
                  <dt>등록 일시</dt>
                  <dd>
                    {new Date(document.created_at).toLocaleString("ko-KR")}
                  </dd>
                </div>
                <div>
                  <dt>문서 식별자</dt>
                  <dd>
                    <code>{document.id}</code>
                  </dd>
                </div>
              </dl>
            </section>
          </div>

          {document.rejection && (
            <section
              className={styles.rejection}
              aria-labelledby="rejection-title"
            >
              <h2 id="rejection-title">입력 거부 안내</h2>
              <p>{document.rejection.message}</p>
            </section>
          )}

          <section
            className={styles.nextStep}
            aria-labelledby="next-step-title"
          >
            <h2 id="next-step-title">다음 작업</h2>
            <p>{nextStep.description}</p>
            <Link href={nextStep.href}>{nextStep.label}</Link>
          </section>
        </div>
      </DocumentWorkspaceShell>
    );
  } catch {
    return (
      <DocumentWorkspaceShell currentSection="overview" documentId={documentId}>
        <section className={styles.error} role="alert">
          <h1>문서 정보를 불러올 수 없습니다</h1>
          <p>문서에 접근할 수 없거나 현재 정보를 확인할 수 없습니다.</p>
          <Link href={`/documents/${documentId}/validation/`}>
            원본 검증 상태 확인
          </Link>
        </section>
      </DocumentWorkspaceShell>
    );
  }
}
