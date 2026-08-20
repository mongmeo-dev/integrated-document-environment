"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  CompileStatus,
  type CompileStatus as CompileStatusValue,
  ConversionStatus,
  type ConversionStatus as ConversionStatusValue,
  RevisionOrigin,
} from "@/api/generated";
import styles from "./document-workbench.module.css";
import {
  useCreateLatexSourceRevisionMutation,
  useLatexPreview,
  useLatexProject,
} from "./use-latex-project";

function errorMessage(error: unknown) {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "status" in error.response &&
    error.response.status === 409
  ) {
    return "다른 사용자가 새 개정본을 만들었습니다. 현재 입력 내용은 유지됩니다. 최신 개정본을 확인한 뒤 필요한 내용을 병합해 다시 저장하세요.";
  }

  return error instanceof Error
    ? `저장 및 컴파일에 실패했습니다: ${error.message}`
    : "저장 및 컴파일에 실패했습니다.";
}

function shortHash(hash: string | null | undefined) {
  return hash ? hash.slice(0, 12) : "없음";
}

function statusLabel(status: CompileStatusValue | ConversionStatusValue) {
  if (status === CompileStatus.Succeeded) return "성공";
  if (status === CompileStatus.Failed) return "실패";
  if (status === CompileStatus.Pending) return "대기";
  if (status === ConversionStatus.PendingReview) return "사람 검토 대기";
  if (status === ConversionStatus.Accepted) return "수락됨";
  if (status === ConversionStatus.Rejected) return "거절됨";
  return "해당 없음";
}

function originLabel(origin: RevisionOrigin) {
  if (origin === RevisionOrigin.LatexUpload) return "LaTeX 업로드";
  if (origin === RevisionOrigin.DocxConversion) return "DOCX 변환";
  return "웹 편집";
}

export function DocumentWorkbench({ documentId }: { documentId: string }) {
  const projectQuery = useLatexProject(documentId);
  const project = projectQuery.data;
  const [source, setSource] = useState("");
  const [baselineSource, setBaselineSource] = useState("");
  const [baselineRevisionId, setBaselineRevisionId] = useState<string | null>(
    null,
  );
  const [saveError, setSaveError] = useState<string | null>(null);
  const [previewObject, setPreviewObject] = useState<{
    revisionId: string;
    url: string;
  } | null>(null);
  const saveRevision = useCreateLatexSourceRevisionMutation(documentId);
  const previewQuery = useLatexPreview(
    documentId,
    project?.revision_id,
    project?.preview_available ?? false,
    project?.compile_status,
  );

  useEffect(() => {
    if (!project) return;
    if (baselineRevisionId === null || source === baselineSource) {
      setSource(project.source);
      setBaselineSource(project.source);
      setBaselineRevisionId(project.revision_id);
    }
  }, [baselineRevisionId, baselineSource, project, source]);

  useEffect(() => {
    if (!previewQuery.data || !project?.revision_id) {
      setPreviewObject(null);
      return;
    }

    const url = URL.createObjectURL(previewQuery.data);
    setPreviewObject({ revisionId: project.revision_id, url });
    return () => URL.revokeObjectURL(url);
  }, [previewQuery.data, project?.revision_id]);

  const isDirty = project !== undefined && source !== baselineSource;
  const diagnostics = project?.compile_log?.slice(0, 12_000);

  async function save() {
    if (!project || saveRevision.isPending) return;

    setSaveError(null);
    try {
      const revision = await saveRevision.mutateAsync({
        expected_revision_id: project.revision_id,
        source,
      });
      setSource(revision.source);
      setBaselineSource(revision.source);
      setBaselineRevisionId(revision.revision_id);
    } catch (error) {
      setSaveError(errorMessage(error));
      await projectQuery.refetch();
    }
  }

  function reset() {
    if (!project || saveRevision.isPending) return;
    setSource(project.source);
    setBaselineSource(project.source);
    setBaselineRevisionId(project.revision_id);
    setSaveError(null);
  }

  if (projectQuery.isLoading) {
    return (
      <output className={styles.loading}>
        LaTeX 프로젝트를 불러오는 중입니다.
      </output>
    );
  }

  if (projectQuery.isError || !project) {
    return (
      <section className={styles.error} aria-labelledby="latex-load-error">
        <h1 id="latex-load-error">LaTeX 프로젝트를 불러올 수 없습니다</h1>
        <p>네트워크 연결과 문서 접근 권한을 확인한 뒤 다시 시도하세요.</p>
        <button onClick={() => void projectQuery.refetch()} type="button">
          다시 시도
        </button>
      </section>
    );
  }

  return (
    <section className={styles.workbench} aria-labelledby="workbench-heading">
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>LaTeX 원본 작업공간</p>
          <h1 id="workbench-heading">{project.entrypoint}</h1>
        </div>
        <dl className={styles.metadata}>
          <div>
            <dt>원본 해시</dt>
            <dd title={project.source_sha256}>
              {shortHash(project.source_sha256)}
            </dd>
          </div>
          <div>
            <dt>PDF 해시</dt>
            <dd title={project.compiled_pdf_sha256 ?? undefined}>
              {shortHash(project.compiled_pdf_sha256)}
            </dd>
          </div>
          <div>
            <dt>원본</dt>
            <dd>{originLabel(project.origin)}</dd>
          </div>
          <div>
            <dt>변환</dt>
            <dd>{statusLabel(project.conversion_status)}</dd>
          </div>
          <div>
            <dt>컴파일</dt>
            <dd>{statusLabel(project.compile_status)}</dd>
          </div>
          <div>
            <dt>편집 상태</dt>
            <dd>{isDirty ? "저장되지 않은 변경" : "저장됨"}</dd>
          </div>
        </dl>
      </header>

      {project.conversion_status === ConversionStatus.PendingReview && (
        <p className={styles.reviewNotice}>
          DOCX 변환 결과는 자동으로 수락되지 않습니다.{" "}
          <Link href={`/documents/${documentId}/import-review/`}>
            사람이 변환을 검토하고 결정하기
          </Link>
        </p>
      )}

      {saveError && (
        <p className={styles.error} role="alert">
          {saveError}
        </p>
      )}

      <div className={styles.panes}>
        <aside className={styles.files} aria-label="LaTeX 번들 파일">
          <h2>번들 파일</h2>
          <ul>
            {project.files.map((file) => (
              <li
                className={
                  file === project.entrypoint ? styles.entrypoint : undefined
                }
                key={file}
              >
                {file}
                {file === project.entrypoint && <span>진입점</span>}
              </li>
            ))}
          </ul>
        </aside>

        <div className={styles.editor}>
          <div className={styles.paneHeader}>
            <h2>원본 편집</h2>
            <div>
              <button
                disabled={!isDirty || saveRevision.isPending}
                onClick={reset}
                type="button"
              >
                되돌리기
              </button>
              <button
                disabled={!isDirty || saveRevision.isPending}
                onClick={() => void save()}
                type="button"
              >
                {saveRevision.isPending
                  ? "저장 및 컴파일 중"
                  : "저장 및 컴파일"}
              </button>
            </div>
          </div>
          <label htmlFor="latex-source">
            진입점 {project.entrypoint}의 LaTeX 원본
          </label>
          <textarea
            id="latex-source"
            onChange={(event) => setSource(event.target.value)}
            spellCheck={false}
            value={source}
          />
        </div>

        <section className={styles.preview} aria-labelledby="preview-heading">
          <h2 id="preview-heading">컴파일 PDF</h2>
          {project.compile_status === CompileStatus.Failed ? (
            <p className={styles.unavailable}>
              컴파일에 실패하여 PDF 미리보기를 제공할 수 없습니다.
            </p>
          ) : !project.preview_available ? (
            <p className={styles.unavailable}>
              이 개정본의 컴파일 PDF가 아직 없습니다.
            </p>
          ) : previewQuery.isLoading ? (
            <p className={styles.unavailable}>
              컴파일 PDF를 불러오는 중입니다.
            </p>
          ) : previewQuery.isError ||
            previewObject?.revisionId !== project.revision_id ? (
            <p className={styles.unavailable}>
              컴파일 PDF 미리보기를 불러올 수 없습니다.
            </p>
          ) : (
            <iframe
              className={styles.pdf}
              src={previewObject.url}
              title={`${project.entrypoint} 컴파일 PDF`}
            />
          )}
          <div className={styles.diagnostics}>
            <h3>컴파일 진단</h3>
            <pre>{diagnostics || "컴파일 로그가 없습니다."}</pre>
          </div>
        </section>
      </div>
    </section>
  );
}
