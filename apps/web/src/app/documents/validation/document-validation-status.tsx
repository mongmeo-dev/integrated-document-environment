"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";

import { documentsApi } from "@/api/client";
import {
  type DocumentResponse,
  DocumentStatus,
  InputKind,
} from "@/api/generated";

import styles from "./validation.module.css";

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const fixtureDocument: DocumentResponse = {
  id: "5e57e8d5-1875-4e31-bf2c-5137f73018c2",
  original_file: {
    id: "89a185d4-bc7b-4d35-a482-058296fe26b1",
    original_filename: "SRS-Core-v2.4.docx",
    media_type:
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    size_bytes: 2846712,
    sha256: "a780e08b1355e577bbcb390eb99e253c6e08a8d6b00e59134f2c71c5390a5d11",
  },
  status: DocumentStatus.Ready,
  input_kind: InputKind.EditableDocx,
  capabilities: {
    analysis: true,
    external_edit_round_trip: true,
    format_comparison: true,
    approved_output: true,
  },
  rejection: null,
  creator: { id: "fixture", display_name: "시안 데이터" },
  created_at: "2026-08-18T09:30:00Z",
};

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
  ["external_edit_round_trip", "외부 편집 왕복", "편집본 재수집 및 차이 확인"],
  ["format_comparison", "형식 비교", "레이아웃·서식 차이 비교"],
  ["approved_output", "승인 산출물", "승인 가능한 출력 생성"],
] as const;

const inputKindCopy = {
  [InputKind.EditableDocx]: "편집 가능 DOCX",
  [InputKind.TextPdf]: "텍스트 PDF",
  [InputKind.ScannedPdf]: "스캔 PDF · 분석 전용",
} as const;

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function rejectionCopy(code: string) {
  const reasons: Record<string, string> = {
    encrypted: "암호화된 원본은 내용을 안전하게 검사할 수 없습니다.",
    corrupt: "원본 구조가 손상되어 신뢰할 수 있는 검증을 완료할 수 없습니다.",
    unsafe_archive:
      "안전하지 않은 보관 파일 구조가 감지되어 처리를 중단했습니다.",
  };
  return reasons[code] ?? "원본이 입력 검증 경계를 통과하지 못했습니다.";
}

export default function DocumentValidationStatus() {
  const [documentId, setDocumentId] = useState("");
  const [document, setDocument] = useState<DocumentResponse>();
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isFixture, setIsFixture] = useState(false);

  const loadDocument = useCallback(async (id: string) => {
    setDocument(undefined);
    setIsFixture(false);
    if (!uuidPattern.test(id)) {
      setError("조회할 문서 UUID를 입력하세요.");
      return;
    }

    setError("");
    setIsLoading(true);
    try {
      const response = await documentsApi.getDocument({ documentId: id });
      const resolved =
        response.data.status === DocumentStatus.Queued
          ? await documentsApi.validateDocument({ documentId: id })
          : response;
      setDocument(resolved.data);
    } catch {
      setError(
        "문서를 조회하지 못했습니다. UUID, 로그인 상태 및 API 연결을 확인하세요.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  const lookupDocument = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void loadDocument(documentId.trim());
  };

  useEffect(() => {
    const id = new URLSearchParams(window.location.search)
      .get("documentId")
      ?.trim();
    if (id && uuidPattern.test(id)) {
      setDocumentId(id);
      void loadDocument(id);
    }
  }, [loadDocument]);

  const showFixture = () => {
    setDocumentId(fixtureDocument.id);
    setDocument(fixtureDocument);
    setError("");
    setIsFixture(true);
  };

  const status = document ? statusCopy[document.status] : undefined;

  return (
    <div className={styles.workspace}>
      <header className={styles.heading}>
        <div>
          <p className={styles.eyebrow}>INGEST / VALIDATION BOUNDARY</p>
          <h1>원본 입력 검증 상태</h1>
          <p>등록된 원본의 처리 가능 범위와 승인 차단 조건을 확인합니다.</p>
        </div>
        <a className={styles.backLink} href="/documents">
          ← 문서 목록
        </a>
      </header>

      <section aria-labelledby="lookup-title" className={styles.lookup}>
        <div>
          <h2 id="lookup-title">문서 UUID 조회</h2>
          <p>
            API: DocumentsApi.getDocument · 등록 ID로 현재 검증 상태를
            조회합니다.
          </p>
        </div>
        <form onSubmit={lookupDocument}>
          <label htmlFor="document-id">문서 UUID</label>
          <div className={styles.lookupControls}>
            <input
              aria-describedby="lookup-hint lookup-error"
              autoComplete="off"
              id="document-id"
              onChange={(event) => setDocumentId(event.target.value)}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={documentId}
            />
            <button disabled={isLoading} type="submit">
              {isLoading ? "조회 중…" : "상태 조회"}
            </button>
          </div>
          <p id="lookup-hint">
            UUID 형식만 조회합니다. 원본 파일은 이 화면에서 전송하지 않습니다.
          </p>
          {error && (
            <p className={styles.error} id="lookup-error" role="alert">
              {error}
            </p>
          )}
        </form>
        <button
          className={styles.fixtureButton}
          onClick={showFixture}
          type="button"
        >
          시안 데이터 보기
        </button>
      </section>

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
        {!document && !isLoading && !error && (
          <div className={styles.empty}>
            <strong>조회 결과 없음</strong>
            <p>
              문서 UUID를 입력하거나 시안 데이터를 열어 검증 결과 형식을
              확인하세요.
            </p>
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
            {isFixture && (
              <p className={styles.fixtureNotice}>
                <strong>시안 데이터</strong> 실제 API 응답이 아닌 화면 검토용
                예시입니다.
              </p>
            )}
            <div className={styles.resultHeading}>
              <div>
                <p className={styles.eyebrow}>DOCUMENT / {document.id}</p>
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
                <h3 id="capability-title">Capability 표</h3>
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
                    <strong>스캔 PDF</strong>는 분석 전용입니다. 외부 편집 왕복,
                    형식 비교 및 승인 산출물에는 사용할 수 없습니다.
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
                <small>API 메시지: {document.rejection.message}</small>
              </section>
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
              <th scope="col">외부 편집 왕복</th>
              <th scope="col">형식 비교</th>
              <th scope="col">승인 산출물</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">
                <code>editable_docx</code>
              </th>
              <td>허용</td>
              <td>허용</td>
              <td>허용</td>
              <td>허용</td>
            </tr>
            <tr>
              <th scope="row">
                <code>text_pdf</code>
              </th>
              <td>허용</td>
              <td>허용</td>
              <td>허용</td>
              <td>허용</td>
            </tr>
            <tr>
              <th scope="row">
                <code>scanned_pdf</code>
              </th>
              <td>허용</td>
              <td>불가</td>
              <td>불가</td>
              <td>불가</td>
            </tr>
          </tbody>
        </table>
        <p>
          <strong>거부 코드</strong> <code>encrypted</code>,{" "}
          <code>corrupt</code>, <code>unsafe_archive</code> 원본은 처리 및
          승인이 불가합니다.
        </p>
      </section>
    </div>
  );
}
