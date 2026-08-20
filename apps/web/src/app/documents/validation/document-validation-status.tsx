"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { documentsApi } from "@/api/client";
import {
  type DocumentResponse,
  DocumentStatus,
  InputKind,
} from "@/api/generated";

import styles from "./validation.module.css";

const statusCopy = {
  [DocumentStatus.Queued]: ["접수 대기", "검증 작업을 대기열에 등록했습니다."],
  [DocumentStatus.Validating]: [
    "검증 진행",
    "입력 유형과 원본 안전성을 판별하고 있습니다.",
  ],
  [DocumentStatus.Ready]: ["검증 완료", "검증 경계 내에서 사용할 수 있습니다."],
  [DocumentStatus.Rejected]: [
    "검증 거부",
    "원본을 처리하지 않았습니다. 거부 사유를 확인하세요.",
  ],
} as const;

const capabilityRows = [
  ["analysis", "분석", "내용 추출 및 근거 분석"],
  ["source_editing", "LaTeX 원본 편집", "Web 작업대의 정본 편집"],
  ["compilation", "PDF 컴파일", "정본에서 PDF 미리보기 생성"],
  ["conversion_review", "변환 검토", "DOCX 변환 후보의 사람 결정"],
  ["approved_output", "승인 산출물", "승인 가능한 출력 생성"],
] as const;

const inputKindCopy = {
  [InputKind.LatexProject]: "LaTeX 프로젝트 · 정본",
  [InputKind.DocxImport]: "DOCX 가져오기 · 변환 검토 필요",
  [InputKind.TextPdf]: "텍스트 PDF · 참조",
  [InputKind.ScannedPdf]: "스캔 PDF · 분석 전용",
} as const;

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function rejectionCopy(code: string) {
  const reasons: Record<string, string> = {
    encrypted_document: "암호화된 원본은 내용을 안전하게 검사할 수 없습니다.",
    corrupt_document:
      "원본 구조가 손상되어 신뢰할 수 있는 검증을 완료할 수 없습니다.",
    unsafe_archive:
      "안전하지 않은 보관 파일 구조가 감지되어 처리를 중단했습니다.",
  };
  return reasons[code] ?? "원본이 입력 검증 경계를 통과하지 못했습니다.";
}

export default function DocumentValidationStatus({
  documentId,
}: {
  documentId: string;
}) {
  const [document, setDocument] = useState<DocumentResponse>();
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const loadDocument = useCallback(async () => {
    setDocument(undefined);
    setError("");
    setIsLoading(true);
    try {
      const response = await documentsApi.getDocument({ documentId });
      const resolved =
        response.data.status === DocumentStatus.Queued
          ? await documentsApi.validateDocument({ documentId })
          : response;
      setDocument(resolved.data);
    } catch {
      setError(
        "문서의 검증 상태를 불러오지 못했습니다. 잠시 후 다시 시도하세요.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    void loadDocument();
  }, [loadDocument]);

  const status = document ? statusCopy[document.status] : undefined;

  return (
    <div className={styles.workspace}>
      <header className={styles.heading}>
        <div>
          <p className={styles.eyebrow}>INGEST / VALIDATION BOUNDARY</p>
          <h1>원본 입력 검증 상태</h1>
          <p>등록된 원본의 처리 가능 범위와 승인 차단 조건을 확인합니다.</p>
        </div>
        <Link className={styles.backLink} href={`/documents/${documentId}/`}>
          문서 개요
        </Link>
      </header>

      <section aria-label="검증 상태 범례" className={styles.statusLegend}>
        {Object.entries(statusCopy).map(([key, [label, description]]) => (
          <div key={key}>
            <span className={`${styles.status} ${styles[`status_${key}`]}`}>
              {label}
            </span>
            <small>{description}</small>
          </div>
        ))}
      </section>

      <section
        className={styles.result}
        id="validation-result"
        aria-live="polite"
      >
        {error && (
          <div className={styles.empty} role="alert">
            <strong>검증 상태를 확인할 수 없음</strong>
            <p>{error}</p>
          </div>
        )}
        {isLoading && (
          <div className={styles.empty}>
            <strong>검증 상태 조회 중</strong>
            <p>등록된 원본의 최신 상태를 가져오고 있습니다.</p>
          </div>
        )}
        {document && status && (
          <>
            <div className={styles.resultHeading}>
              <div>
                <p className={styles.eyebrow}>DOCUMENT VALIDATION</p>
                <h2>{document.original_file.original_filename}</h2>
              </div>
              <span
                className={`${styles.status} ${styles[`status_${document.status}`]}`}
              >
                {status[0]}
              </span>
            </div>
            <p className={styles.statusDescription}>{status[1]}</p>
            {(document.status === DocumentStatus.Queued ||
              document.status === DocumentStatus.Validating) && (
              <p className={styles.blockingNotice}>
                <strong>승인 차단</strong> 검증이 완료되기 전에는 승인 산출물을
                생성하거나 승인 절차를 진행할 수 없습니다.
              </p>
            )}
            <div className={styles.detailsGrid}>
              <section
                aria-labelledby="original-title"
                className={styles.panel}
              >
                <h3 id="original-title">원본 지문</h3>
                <dl className={styles.metadata}>
                  <div>
                    <dt>SHA-256</dt>
                    <dd>
                      <code>{document.original_file.sha256}</code>
                    </dd>
                  </div>
                  <div>
                    <dt>크기</dt>
                    <dd>
                      {formatBytes(document.original_file.size_bytes)}{" "}
                      <small>
                        ({document.original_file.size_bytes.toLocaleString()}{" "}
                        bytes)
                      </small>
                    </dd>
                  </div>
                  <div>
                    <dt>미디어 형식</dt>
                    <dd>
                      <code>{document.original_file.media_type}</code>
                    </dd>
                  </div>
                  <div>
                    <dt>입력 유형</dt>
                    <dd>
                      {document.input_kind
                        ? inputKindCopy[document.input_kind]
                        : "판별 중 또는 거부됨"}
                    </dd>
                  </div>
                </dl>
              </section>
              <section
                aria-labelledby="capability-title"
                className={styles.panel}
              >
                <h3 id="capability-title">사용 가능 범위</h3>
                <table>
                  <thead>
                    <tr>
                      <th scope="col">범위</th>
                      <th scope="col">설명</th>
                      <th scope="col">현재</th>
                    </tr>
                  </thead>
                  <tbody>
                    {capabilityRows.map(([key, label, description]) => (
                      <tr key={key}>
                        <th scope="row">{label}</th>
                        <td>{description}</td>
                        <td>{document.capabilities[key] ? "허용" : "불가"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {document.input_kind === InputKind.ScannedPdf && (
                  <p className={styles.scanNote}>
                    <strong>스캔 PDF</strong>는 분석 전용입니다. LaTeX 정본
                    편집, 컴파일 및 승인 산출물에는 사용할 수 없습니다.
                  </p>
                )}
              </section>
            </div>
            {document.rejection && (
              <section
                aria-labelledby="rejection-title"
                className={styles.rejection}
              >
                <h3 id="rejection-title">
                  거부 사유 · {document.rejection.code}
                </h3>
                <p>{rejectionCopy(document.rejection.code)}</p>
                <small>상세 메시지: {document.rejection.message}</small>
              </section>
            )}
            {document.status === DocumentStatus.Ready && (
              <Link
                className={styles.nextStepLink}
                href={
                  document.input_kind === InputKind.LatexProject ||
                  document.input_kind === InputKind.DocxImport
                    ? `/documents/${document.id}/workbench/`
                    : `/documents/${document.id}/changes/`
                }
              >
                {document.input_kind === InputKind.LatexProject ||
                document.input_kind === InputKind.DocxImport
                  ? "LaTeX 작업대로 계속"
                  : "분석 결과 검토로 계속"}
              </Link>
            )}
          </>
        )}
      </section>

      <section aria-labelledby="boundary-title" className={styles.boundary}>
        <h2 id="boundary-title">입력 경계 참조</h2>
        <table>
          <thead>
            <tr>
              <th scope="col">입력 유형</th>
              <th scope="col">분석</th>
              <th scope="col">LaTeX 편집</th>
              <th scope="col">컴파일</th>
              <th scope="col">변환 검토</th>
              <th scope="col">승인 산출물</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">
                <code>latex_project</code>
              </th>
              <td>허용</td>
              <td>허용</td>
              <td>허용</td>
              <td>해당 없음</td>
              <td>허용</td>
            </tr>
            <tr>
              <th scope="row">
                <code>docx_import</code>
              </th>
              <td>허용</td>
              <td>허용</td>
              <td>허용</td>
              <td>필수</td>
              <td>검토 전 불가</td>
            </tr>
            <tr>
              <th scope="row">
                <code>text_pdf / scanned_pdf</code>
              </th>
              <td>허용</td>
              <td>불가</td>
              <td>불가</td>
              <td>불가</td>
              <td>불가</td>
            </tr>
          </tbody>
        </table>
        <p>
          <strong>거부 코드</strong> <code>encrypted_document</code>,{" "}
          <code>corrupt_document</code>, <code>unsafe_archive</code> 원본은 처리
          및 승인이 불가합니다.
        </p>
      </section>
    </div>
  );
}
