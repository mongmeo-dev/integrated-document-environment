"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { formattingApi } from "@/api/client";
import {
  type ExternalEditResultResponse,
  ExternalEditResultStatus,
  type FormatCheckResponse,
  FormatDifferenceCategory,
  type FormatDifferenceResponse,
  OriginalFormat,
  VisualReviewStatus,
} from "@/api/generated";

import styles from "./formatting.module.css";

const fixtureDocumentId = "ND-SRS-002";
const fixtureVersionId = "version-2026-08-18-01";

const categoryLabels = {
  [FormatDifferenceCategory.Font]: "폰트",
  [FormatDifferenceCategory.Color]: "색상",
  [FormatDifferenceCategory.Table]: "표",
  [FormatDifferenceCategory.Margin]: "여백",
  [FormatDifferenceCategory.LineSpacing]: "줄간격",
  [FormatDifferenceCategory.FontSize]: "크기",
  [FormatDifferenceCategory.Other]: "기타",
};

const fixtureDifferences: FormatDifferenceResponse[] = [
  {
    id: "fixture-diff-font",
    format_check_id: "fixture-format-check-002",
    category: FormatDifferenceCategory.Font,
    location: "§ 2.1 · 첫 번째 문단",
    original_value: "Noto Sans KR 10pt",
    proposed_value: "Arial 10pt",
    resolved: false,
    created_at: "2026-08-18T08:31:00Z",
  },
  {
    id: "fixture-diff-color",
    format_check_id: "fixture-format-check-002",
    category: FormatDifferenceCategory.Color,
    location: "§ 3.2 · 경고 문구",
    original_value: "#B42318",
    proposed_value: "#D92D20",
    resolved: false,
    created_at: "2026-08-18T08:31:00Z",
  },
  {
    id: "fixture-diff-table",
    format_check_id: "fixture-format-check-002",
    category: FormatDifferenceCategory.Table,
    location: "표 4 · 역할 매트릭스",
    original_value: "열 5개 · 테두리 0.5pt",
    proposed_value: "열 4개 · 테두리 없음",
    resolved: false,
    created_at: "2026-08-18T08:31:00Z",
  },
  {
    id: "fixture-diff-margin",
    format_check_id: "fixture-format-check-002",
    category: FormatDifferenceCategory.Margin,
    location: "p. 6 · 하단",
    original_value: "20 mm",
    proposed_value: "25 mm",
    resolved: true,
    created_at: "2026-08-18T08:31:00Z",
  },
  {
    id: "fixture-diff-line-spacing",
    format_check_id: "fixture-format-check-002",
    category: FormatDifferenceCategory.LineSpacing,
    location: "§ 4.1 · 검증 절차",
    original_value: "1.5줄",
    proposed_value: "1.15줄",
    resolved: false,
    created_at: "2026-08-18T08:31:00Z",
  },
  {
    id: "fixture-diff-font-size",
    format_check_id: "fixture-format-check-002",
    category: FormatDifferenceCategory.FontSize,
    location: "§ 1 · 제목",
    original_value: "16pt",
    proposed_value: "14pt",
    resolved: false,
    created_at: "2026-08-18T08:31:00Z",
  },
];

const fixtureCheck: FormatCheckResponse = {
  id: "fixture-format-check-002",
  external_edit_result_id: "fixture-external-result-002",
  automatic_check_completed: true,
  visual_review: VisualReviewStatus.Pending,
  unresolved_difference_count: 5,
  created_at: "2026-08-18T08:30:00Z",
  updated_at: "2026-08-18T08:31:00Z",
  differences: fixtureDifferences,
};

const fixtureResult: ExternalEditResultResponse = {
  id: "fixture-external-result-002",
  document_id: fixtureDocumentId,
  document_version_id: fixtureVersionId,
  original_format: OriginalFormat.Docx,
  original_filename: "ND-SRS-002_사용자-접근-통제.docx",
  media_type:
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  size_bytes: 2846712,
  sha256: "a780e08b1355e577bbcb390eb99e253c6e08a8d6b00e59134f2c71c5390a5d11",
  object_key: "external-results/ND-SRS-002/recollected-v2.docx",
  status: ExternalEditResultStatus.NeedsRevision,
  created_by_id: "user-km",
  created_at: "2026-08-18T08:30:00Z",
  format_check: fixtureCheck,
};

function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "API 요청을 완료하지 못했습니다.";
}

function reviewLabel(status: FormatCheckResponse["visual_review"]) {
  if (status === VisualReviewStatus.Passed) return "통과";
  if (status === VisualReviewStatus.Failed) return "실패";
  return "대기";
}

function resultStatusLabel(status: ExternalEditResultResponse["status"]) {
  if (status === ExternalEditResultStatus.Uploaded) return "수집됨";
  if (status === ExternalEditResultStatus.Checking) return "검사 중";
  if (status === ExternalEditResultStatus.NeedsRevision) return "수정 필요";
  return "통과";
}

export function FormattingWorkspace() {
  const [searchParams] = useState(
    () =>
      new URLSearchParams(
        typeof window === "undefined" ? "" : window.location.search,
      ),
  );
  const documentId = searchParams.get("documentId");
  const externalResultId = searchParams.get("externalResultId");
  const [result, setResult] = useState<ExternalEditResultResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [empty, setEmpty] = useState<string | null>(null);
  const [action, setAction] = useState<string | null>(null);
  const [showFixture, setShowFixture] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadResult = useCallback(async () => {
    if (showFixture) {
      setResult(fixtureResult);
      setEmpty(null);
      return;
    }
    if (!externalResultId && !documentId) {
      setResult(null);
      setEmpty(null);
      return;
    }
    setLoading(true);
    setError(null);
    setEmpty(null);
    try {
      if (externalResultId) {
        const response = await formattingApi.getExternalEditResult({
          externalEditResultId: externalResultId,
        });
        setResult(response.data);
      } else {
        const response = await formattingApi.listExternalEditResults({
          documentId: documentId as string,
        });
        setResult(response.data[0] ?? null);
        if (response.data.length === 0) {
          setEmpty("조회 가능한 외부 편집 결과가 없습니다.");
        }
      }
    } catch (requestError) {
      setError(
        `외부 편집 결과를 불러오지 못했습니다: ${errorMessage(requestError)}`,
      );
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [documentId, externalResultId, showFixture]);

  useEffect(() => {
    void loadResult();
  }, [loadResult]);

  const comparisonRows = useMemo(
    () =>
      result
        ? ([
            ["원본", result.original_filename, "DOCX · 기준 파일"],
            ["외부 결과", "recollected-v2.docx", "DOCX · 외부 편집 재수집본"],
          ] as const)
        : [],
    [result],
  );

  if (!result) {
    return (
      <div className={styles.workspace} id="formatting-workspace">
        <section className={styles.intro} aria-busy={loading}>
          <h1>외부 편집 결과 서식 검토</h1>
          {loading && (
            <output className={styles.loading}>
              외부 편집 결과를 불러오는 중입니다.
            </output>
          )}
          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}
          {empty && <p>{empty}</p>}
          {!loading && !error && (
            <>
              {!empty && (
                <p>
                  URL에 documentId 또는 externalResultId를 지정해 결과를
                  조회하세요.
                </p>
              )}
              <button onClick={() => setShowFixture(true)} type="button">
                시안 보기
              </button>
            </>
          )}
        </section>
      </div>
    );
  }

  const activeResult = result;
  const check = result.format_check;
  const differences = check.differences ?? [];
  const unresolved = differences.filter((difference) => !difference.resolved);
  const unresolvedCount = Math.max(
    check.unresolved_difference_count,
    unresolved.length,
  );
  const approvalAllowed =
    check.automatic_check_completed &&
    check.visual_review === VisualReviewStatus.Passed &&
    unresolvedCount === 0;

  async function runAutomaticCheck() {
    setAction("check");
    setError(null);
    try {
      await formattingApi.runExternalResultAutomaticFormatCheck({
        externalEditResultId: activeResult.id,
      });
      await loadResult();
    } catch (requestError) {
      setError(`자동 검사 요청이 실패했습니다: ${errorMessage(requestError)}`);
    } finally {
      setAction(null);
    }
  }

  async function completeVisualReview(status: VisualReviewStatus) {
    setAction(`review-${status}`);
    setError(null);
    try {
      await formattingApi.completeExternalResultVisualReview({
        externalEditResultId: activeResult.id,
        bodyCompleteExternalResultVisualReview: { visual_review: status },
      });
      await loadResult();
    } catch (requestError) {
      setError(`시각 검토 기록이 실패했습니다: ${errorMessage(requestError)}`);
    } finally {
      setAction(null);
    }
  }

  async function resolveDifference(differenceId: string) {
    setAction(differenceId);
    setError(null);
    try {
      await formattingApi.resolveExternalResultFormatDifference({
        differenceId,
      });
      await loadResult();
    } catch (requestError) {
      setError(`차이 해결 기록이 실패했습니다: ${errorMessage(requestError)}`);
    } finally {
      setAction(null);
    }
  }

  async function recollect(file: File | null) {
    if (!file) {
      setError("재수집할 파일을 선택하세요.");
      return;
    }
    setAction("recollect");
    setError(null);
    try {
      const collected = await formattingApi.collectExternalEditResult({
        documentId: activeResult.document_id,
        documentVersionId: activeResult.document_version_id,
        file,
      });
      const collectedId = (collected.data as { id?: string }).id;
      if (collectedId) {
        const refreshed = await formattingApi.getExternalEditResult({
          externalEditResultId: collectedId,
        });
        setResult(refreshed.data);
      } else {
        await loadResult();
      }
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (requestError) {
      setError(
        `외부 결과 재수집이 실패했습니다: ${errorMessage(requestError)}`,
      );
    } finally {
      setAction(null);
    }
  }

  return (
    <div className={styles.workspace} id="formatting-workspace">
      <section className={styles.intro} aria-labelledby="formatting-heading">
        <div>
          <p className={styles.eyebrow}>
            외부 편집 결과 재수집 ·{" "}
            {showFixture && (
              <span className={styles.fixtureBadge}>Fixture</span>
            )}
          </p>
          <h1 id="formatting-heading">원본 대비 자동 서식 검사 · 시각 비교</h1>
          <p>
            원본과 같은 DOCX 형식으로 재수집한 결과만 비교합니다. 색상 외의 서식
            차이와 위치를 모두 검토해야 합니다.
          </p>
        </div>
        <div className={styles.resultState}>
          <strong>재수집 상태: {resultStatusLabel(result.status)}</strong>
          <span>결과 ID {result.id}</span>
        </div>
      </section>

      {loading && (
        <output className={styles.loading}>
          FormattingApi 결과를 불러오는 중입니다.
        </output>
      )}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      <section className={styles.boundary} aria-labelledby="boundary-heading">
        <div>
          <p className={styles.sectionLabel}>형식 경계</p>
          <h2 id="boundary-heading">같은 형식의 편집 가능 파일만 비교</h2>
        </div>
        <ul>
          <li>
            <strong>허용:</strong> DOCX 원본 → DOCX 외부 결과
          </li>
          <li>
            <strong>차단:</strong> 스캔 PDF는 텍스트·서식 구조가 없어 비교할 수
            없습니다.
          </li>
          <li>
            <strong>차단:</strong> DOCX ↔ PDF 등 교차 형식 결과는 승인 대상이
            아닙니다.
          </li>
        </ul>
      </section>

      <section className={styles.statusGrid} aria-label="검사와 승인 상태">
        <article className={styles.statusCard}>
          <p>자동 서식 검사</p>
          <strong>{check.automatic_check_completed ? "완료" : "미완료"}</strong>
          <span>폰트·색상·표·여백·줄간격·크기를 구조적으로 검사</span>
          <button
            disabled={action !== null}
            onClick={runAutomaticCheck}
            type="button"
          >
            {action === "check" ? "자동 검사 중" : "자동 검사 재실행"}
          </button>
        </article>
        <article className={styles.statusCard}>
          <p>시각 비교 검토</p>
          <strong
            className={
              check.visual_review === VisualReviewStatus.Passed
                ? styles.pass
                : styles.pending
            }
          >
            {reviewLabel(check.visual_review)}
          </strong>
          <span>원본과 결과 패널을 사람의 눈으로 대조</span>
          <div className={styles.buttonRow}>
            <button
              disabled={action !== null}
              onClick={() => completeVisualReview(VisualReviewStatus.Passed)}
              type="button"
            >
              통과 기록
            </button>
            <button
              className={styles.secondaryButton}
              disabled={action !== null}
              onClick={() => completeVisualReview(VisualReviewStatus.Failed)}
              type="button"
            >
              실패 기록
            </button>
          </div>
        </article>
        <article className={styles.statusCard}>
          <p>미해결 차이</p>
          <strong className={unresolvedCount === 0 ? styles.pass : styles.fail}>
            {unresolvedCount}건
          </strong>
          <span>해결 기록된 항목까지 포함하여 승인 조건을 계산</span>
        </article>
      </section>

      <section
        className={styles.comparison}
        aria-labelledby="comparison-heading"
      >
        <div className={styles.sectionHeading}>
          <div>
            <p className={styles.sectionLabel}>시각 비교 패널</p>
            <h2 id="comparison-heading">원본 / 외부 결과</h2>
          </div>
          <span>색상만이 아닌 배치·치수·글꼴을 대조</span>
        </div>
        <div className={styles.compareGrid}>
          {comparisonRows.map(([label, filename, descriptor], index) => (
            <article className={styles.documentPanel} key={label}>
              <header>
                <strong>{label}</strong>
                <span>{descriptor}</span>
              </header>
              <div
                className={
                  index === 0 ? styles.paperOriginal : styles.paperResult
                }
              >
                <p className={styles.documentTitle}>사용자 접근 통제</p>
                <div className={styles.documentRule} />
                <p className={styles.documentText}>
                  2.1 사용자 계정은 권한과 역할에 따라 관리한다.
                </p>
                <p className={styles.documentText}>
                  변경된 접근 권한은 감사 로그에 기록한다.
                </p>
                <div className={styles.documentTable}>
                  <span>역할</span>
                  <span>권한</span>
                  <span>승인</span>
                </div>
                <p className={styles.documentFooter}>p. 6 · {filename}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        className={styles.differenceSection}
        aria-labelledby="difference-heading"
      >
        <div className={styles.sectionHeading}>
          <div>
            <p className={styles.sectionLabel}>자동 검사 결과</p>
            <h2 id="difference-heading">서식 차이와 위치</h2>
          </div>
          <span>
            {differences.length}건 탐지 · 미해결 {unresolvedCount}건
          </span>
        </div>
        <ul className={styles.differenceList}>
          {differences.map((difference) => (
            <li
              className={difference.resolved ? styles.resolved : ""}
              key={difference.id}
            >
              <div>
                <strong>{categoryLabels[difference.category]}</strong>
                <span>{difference.location}</span>
              </div>
              <p>
                <del>{difference.original_value}</del>
                <span aria-hidden="true">→</span>
                <ins>{difference.proposed_value}</ins>
              </p>
              <button
                disabled={difference.resolved || action !== null}
                onClick={() => resolveDifference(difference.id)}
                type="button"
              >
                {difference.resolved
                  ? "해결됨"
                  : action === difference.id
                    ? "기록 중"
                    : "해결 기록"}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.approvalGate} aria-labelledby="gate-heading">
        <div>
          <p className={styles.sectionLabel}>승인 게이트</p>
          <h2 id="gate-heading">
            {approvalAllowed ? "승인 가능" : "승인 차단"}
          </h2>
          <p>
            자동 검사 완료, 시각 비교 통과, 미해결 차이 0건이 모두 충족될 때만
            통과합니다. 하나라도 충족하지 않으면 승인할 수 없습니다.
          </p>
        </div>
        <div className={styles.gateChecks}>
          <span
            className={
              check.automatic_check_completed ? styles.met : styles.unmet
            }
          >
            자동 검사 {check.automatic_check_completed ? "완료" : "미완료"}
          </span>
          <span
            className={
              check.visual_review === VisualReviewStatus.Passed
                ? styles.met
                : styles.unmet
            }
          >
            시각 검토 {reviewLabel(check.visual_review)}
          </span>
          <span className={unresolvedCount === 0 ? styles.met : styles.unmet}>
            미해결 {unresolvedCount}건
          </span>
        </div>
      </section>

      <section className={styles.recollect} aria-labelledby="recollect-heading">
        <div>
          <p className={styles.sectionLabel}>반복 재수집</p>
          <h2 id="recollect-heading">수정된 외부 결과를 다시 수집</h2>
          <p>
            결과 파일이 저장소에 업로드된 뒤 같은 DOCX 형식과 원본 SHA-256
            연결로 재수집합니다.
          </p>
        </div>
        <input
          accept={result.media_type}
          aria-label="재수집할 외부 편집 결과 파일"
          disabled={action !== null}
          ref={fileInputRef}
          type="file"
        />
        <button
          disabled={action !== null}
          onClick={() => recollect(fileInputRef.current?.files?.[0] ?? null)}
          type="button"
        >
          {action === "recollect" ? "재수집 등록 중" : "외부 결과 재수집 반복"}
        </button>
      </section>
    </div>
  );
}
