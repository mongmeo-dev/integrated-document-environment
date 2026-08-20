"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { evidenceApi } from "@/api/client";
import {
  type DocumentEvidenceLinkResponse,
  EvidenceFreshness,
  type EvidenceItemResponse,
  EvidenceLinkStatus,
  EvidenceType,
} from "@/api/generated";

import styles from "./evidence.module.css";

type Evidence = {
  id: string;
  type: (typeof EvidenceType)[keyof typeof EvidenceType];
  title: string;
  description: string;
  reference: string;
  location: string;
  version: string;
  document: string;
  documentLocation: string;
  linkId: string;
  status: (typeof EvidenceLinkStatus)[keyof typeof EvidenceLinkStatus];
  freshness: (typeof EvidenceFreshness)[keyof typeof EvidenceFreshness];
};

const typeLabel = {
  [EvidenceType.Upload]: "업로드",
  [EvidenceType.Description]: "설명",
  [EvidenceType.AppSnapshot]: "앱",
  [EvidenceType.WebSnapshot]: "웹",
  [EvidenceType.ServerCode]: "서버",
  [EvidenceType.Database]: "DB",
  [EvidenceType.CloudConfig]: "클라우드",
  [EvidenceType.TestResult]: "테스트",
};

const statusLabel = {
  [EvidenceLinkStatus.Candidate]: "후보",
  [EvidenceLinkStatus.Confirmed]: "확정",
  [EvidenceLinkStatus.Rejected]: "거절",
};

function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "API 요청을 완료하지 못했습니다.";
}

function FreshnessBadge({ freshness }: { freshness: Evidence["freshness"] }) {
  return (
    <span
      className={
        freshness === EvidenceFreshness.Stale ? styles.stale : styles.current
      }
    >
      <span aria-hidden="true">
        {freshness === EvidenceFreshness.Stale ? "!" : "●"}
      </span>
      {freshness === EvidenceFreshness.Stale ? "오래됨" : "현재"}
    </span>
  );
}

function mapEvidence(
  link: DocumentEvidenceLinkResponse,
  evidence: EvidenceItemResponse,
): Evidence {
  return {
    id: link.id,
    type: evidence.evidence_type,
    title: evidence.title,
    description: evidence.description,
    reference: evidence.reference ?? "참조 없음",
    location: evidence.location ?? "위치 없음",
    version: evidence.version ?? "버전 정보 없음",
    document: "현재 문서",
    documentLocation: link.reason,
    linkId: link.id,
    status: link.status,
    freshness: link.freshness,
  };
}

export function EvidenceWorkspace({ documentId }: { documentId: string }) {
  const [items, setItems] = useState<Evidence[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<"전체" | Evidence["type"]>(
    "전체",
  );
  const [freshnessFilter, setFreshnessFilter] = useState<
    "전체" | Evidence["freshness"]
  >("전체");
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadDescription, setUploadDescription] = useState("");
  const [uploadVersion, setUploadVersion] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadedEvidence, setUploadedEvidence] =
    useState<EvidenceItemResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [linkReason, setLinkReason] = useState("");
  const [linkError, setLinkError] = useState<string | null>(null);
  const [isCreatingLink, setIsCreatingLink] = useState(false);
  const [createdLinkId, setCreatedLinkId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const requestIdRef = useRef(0);

  const loadDocumentEvidence = useCallback(async (nextDocumentId: string) => {
    const requestId = ++requestIdRef.current;
    setIsLoading(true);
    setError(null);
    setItems([]);
    setSelectedId(null);
    try {
      const { data: links } =
        await evidenceApi.listDocumentEvidenceLinkCandidates({
          documentId: nextDocumentId,
        });
      const evidence = await Promise.all(
        links.map(async (link) => {
          const { data: item } = await evidenceApi.getEvidenceItem({
            evidenceId: link.evidence_id,
          });
          return mapEvidence(link, item);
        }),
      );
      if (requestId !== requestIdRef.current) return;
      setItems(evidence);
      setSelectedId(evidence[0]?.id ?? null);
    } catch (requestError) {
      if (requestId !== requestIdRef.current) return;
      setError(
        `문서 근거 목록을 불러오지 못했습니다: ${errorMessage(requestError)}`,
      );
    } finally {
      if (requestId === requestIdRef.current) {
        setHasLoaded(true);
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void loadDocumentEvidence(documentId);
  }, [documentId, loadDocumentEvidence]);

  const visibleItems = useMemo(
    () =>
      items.filter(
        (item) =>
          (typeFilter === "전체" || item.type === typeFilter) &&
          (freshnessFilter === "전체" || item.freshness === freshnessFilter),
      ),
    [freshnessFilter, items, typeFilter],
  );
  const selected = items.find((item) => item.id === selectedId) ?? null;

  async function performAction(action: "confirm" | "reject" | "review") {
    if (
      !selected ||
      (action === "confirm" && selected.freshness === EvidenceFreshness.Stale)
    )
      return;

    setPendingAction(action);
    setError(null);
    try {
      if (action === "confirm") {
        await evidenceApi.confirmDocumentEvidenceLinkCandidate({
          linkId: selected.linkId,
        });
      } else if (action === "reject") {
        await evidenceApi.rejectDocumentEvidenceLinkCandidate({
          linkId: selected.linkId,
        });
      } else {
        await evidenceApi.reviewDocumentEvidenceLinkFreshness({
          linkId: selected.linkId,
        });
      }
      await loadDocumentEvidence(documentId);
    } catch (requestError) {
      setError(
        `근거 조치를 완료하지 못했습니다: ${errorMessage(requestError)}`,
      );
    } finally {
      setPendingAction(null);
    }
  }

  async function uploadEvidenceFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!uploadTitle.trim() || !uploadDescription.trim()) {
      setUploadError("제목과 설명을 입력하세요.");
      return;
    }
    if (!uploadFile) {
      setUploadError("업로드할 파일을 선택하세요.");
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setLinkError(null);
    setCreatedLinkId(null);
    try {
      const { data } = await evidenceApi.createEvidenceFile({
        title: uploadTitle.trim(),
        description: uploadDescription.trim(),
        file: uploadFile,
        version: uploadVersion.trim() || undefined,
      });
      setUploadedEvidence(data);
      setLinkReason("");
    } catch (requestError) {
      setUploadError(
        `파일 근거를 등록하지 못했습니다: ${errorMessage(requestError)}`,
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function createLinkCandidate() {
    if (!uploadedEvidence) return;

    const reason = linkReason.trim();
    if (!reason) {
      setLinkError("연결 후보를 만드는 이유를 입력하세요.");
      return;
    }

    setIsCreatingLink(true);
    setLinkError(null);
    setCreatedLinkId(null);
    try {
      const { data } = await evidenceApi.createDocumentEvidenceLinkCandidate({
        documentEvidenceLinkCreate: {
          document_id: documentId,
          evidence_id: uploadedEvidence.id,
          reason,
        },
      });
      setCreatedLinkId(data.id);
      await loadDocumentEvidence(documentId);
    } catch (requestError) {
      setLinkError(
        `연결 후보를 만들지 못했습니다: ${errorMessage(requestError)}`,
      );
    } finally {
      setIsCreatingLink(false);
    }
  }

  return (
    <div className={styles.workspace}>
      <aside className={styles.filters} aria-label="근거 필터">
        <div className={styles.panelHeading}>
          <div>
            <p className={styles.eyebrow}>문서별 검토</p>
            <h1>근거 후보 검토</h1>
          </div>
        </div>
        <p className={styles.documentNote}>
          이 문서에 연결된 근거 후보를 검토하고 명시적으로 결정합니다.
        </p>
        <fieldset>
          <legend>근거 유형</legend>
          {(["전체", ...Object.values(EvidenceType)] as const).map((value) => (
            <label key={value}>
              <input
                checked={typeFilter === value}
                name="type"
                onChange={() => setTypeFilter(value)}
                type="radio"
              />
              {value === "전체" ? value : typeLabel[value]}
            </label>
          ))}
        </fieldset>
        <fieldset>
          <legend>최신성</legend>
          {(
            [
              "전체",
              EvidenceFreshness.Current,
              EvidenceFreshness.Stale,
            ] as const
          ).map((value) => (
            <label key={value}>
              <input
                checked={freshnessFilter === value}
                name="freshness"
                onChange={() => setFreshnessFilter(value)}
                type="radio"
              />
              {value === "전체"
                ? value
                : value === EvidenceFreshness.Stale
                  ? "오래됨"
                  : "현재"}
            </label>
          ))}
        </fieldset>
        <details className={styles.uploadDetails}>
          <summary>새 파일 근거 등록</summary>
          <form
            className={styles.uploadForm}
            onSubmit={uploadEvidenceFile}
            aria-label="파일 근거 등록"
          >
            <p>검토할 파일을 등록한 뒤 이 문서의 연결 후보로 추가합니다.</p>
            <label htmlFor="evidence-upload-title">제목</label>
            <input
              id="evidence-upload-title"
              onChange={(event) => setUploadTitle(event.target.value)}
              required
              value={uploadTitle}
            />
            <label htmlFor="evidence-upload-description">설명</label>
            <textarea
              id="evidence-upload-description"
              onChange={(event) => setUploadDescription(event.target.value)}
              required
              rows={3}
              value={uploadDescription}
            />
            <label htmlFor="evidence-upload-version">버전 (선택)</label>
            <input
              id="evidence-upload-version"
              onChange={(event) => setUploadVersion(event.target.value)}
              value={uploadVersion}
            />
            <label htmlFor="evidence-upload-file">파일</label>
            <input
              id="evidence-upload-file"
              onChange={(event) =>
                setUploadFile(event.target.files?.[0] ?? null)
              }
              required
              type="file"
            />
            <button disabled={isUploading} type="submit">
              {isUploading ? "파일 등록 중…" : "파일 등록"}
            </button>
            {uploadError && (
              <p className={styles.error} role="alert">
                {uploadError}
              </p>
            )}
          </form>
          {uploadedEvidence && (
            <section className={styles.uploadSuccess} aria-live="polite">
              <h2>파일 근거가 등록되었습니다</h2>
              <p>
                <strong>{uploadedEvidence.title}</strong>
                <br />
                {uploadedEvidence.description}
              </p>
              <dl>
                <div>
                  <dt>유형</dt>
                  <dd>{typeLabel[uploadedEvidence.evidence_type]}</dd>
                </div>
                {uploadedEvidence.version && (
                  <div>
                    <dt>버전</dt>
                    <dd>{uploadedEvidence.version}</dd>
                  </div>
                )}
              </dl>
              <a
                href={`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/v1/evidence/${uploadedEvidence.id}/file`}
              >
                등록한 파일 다운로드
              </a>
              <div className={styles.linkCandidate}>
                <label htmlFor="evidence-link-reason">
                  이 문서에 연결하는 이유
                </label>
                <textarea
                  id="evidence-link-reason"
                  onChange={(event) => setLinkReason(event.target.value)}
                  rows={3}
                  value={linkReason}
                />
                <button
                  disabled={isCreatingLink}
                  onClick={createLinkCandidate}
                  type="button"
                >
                  {isCreatingLink ? "후보 추가 중…" : "문서 근거 후보로 추가"}
                </button>
                {linkError && (
                  <p className={styles.error} role="alert">
                    {linkError}
                  </p>
                )}
                {createdLinkId && (
                  <p className={styles.success}>
                    문서 근거 후보에 추가했습니다.
                  </p>
                )}
              </div>
            </section>
          )}
        </details>
      </aside>

      <section className={styles.mainPanel} aria-labelledby="evidence-heading">
        <div className={styles.mainHeading}>
          <div>
            <p className={styles.eyebrow}>검토 대상 {visibleItems.length}건</p>
            <h2 id="evidence-heading">문서 근거 후보</h2>
          </div>
          <p className={styles.noAutoConfirm}>자동 확정 없음</p>
        </div>
        <p className={styles.staleRule}>
          <strong>오래됨</strong> 근거는 확정할 수 없습니다. 현재성 검토 후
          확정하며, 관련 문서·제품·검증 변경이 발생하면 다시 오래됨으로
          열립니다.
        </p>
        <ol
          className={styles.evidenceList}
          id="evidence-list"
          aria-label="근거 후보 목록"
        >
          {visibleItems.map((item) => (
            <li key={item.id}>
              <button
                aria-current={item.id === selected?.id ? "true" : undefined}
                className={
                  item.id === selected?.id ? styles.selected : undefined
                }
                onClick={() => {
                  setSelectedId(item.id);
                  setError(null);
                }}
                type="button"
              >
                <span className={styles.typeIcon} aria-hidden="true">
                  {typeLabel[item.type].slice(0, 1)}
                </span>
                <span className={styles.listCopy}>
                  <strong>{item.title}</strong>
                  <span>
                    {item.document} · {item.documentLocation}
                  </span>
                  <small>
                    {typeLabel[item.type]} · {statusLabel[item.status]} ·{" "}
                    {item.version}
                  </small>
                </span>
                <FreshnessBadge freshness={item.freshness} />
              </button>
            </li>
          ))}
          {isLoading && (
            <li className={styles.empty}>문서 근거를 불러오는 중입니다.</li>
          )}
          {!isLoading && visibleItems.length === 0 && (
            <li className={styles.empty}>
              {hasLoaded
                ? "선택한 조건에 맞는 근거가 없습니다."
                : "문서 근거를 불러오고 있습니다."}
            </li>
          )}
        </ol>
      </section>

      <aside
        className={styles.detail}
        aria-label="선택한 근거 상세"
        aria-live="polite"
      >
        <p className={styles.eyebrow}>선택 근거</p>
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        {selected ? (
          <>
            <div className={styles.detailHeading}>
              <span className={styles.typeIcon} aria-hidden="true">
                {typeLabel[selected.type].slice(0, 1)}
              </span>
              <div>
                <h2>{selected.title}</h2>
                <p>
                  {typeLabel[selected.type]} · {statusLabel[selected.status]}
                </p>
              </div>
            </div>
            <FreshnessBadge freshness={selected.freshness} />
            <p className={styles.description}>{selected.description}</p>
            <dl>
              <div>
                <dt>연결 문서 후보</dt>
                <dd>
                  {selected.document}
                  <br />
                  {selected.documentLocation}
                </dd>
              </div>
              <div>
                <dt>참조</dt>
                <dd>{selected.reference}</dd>
              </div>
              <div>
                <dt>위치</dt>
                <dd>{selected.location}</dd>
              </div>
              <div>
                <dt>버전</dt>
                <dd>{selected.version}</dd>
              </div>
            </dl>
            {selected.freshness === EvidenceFreshness.Stale && (
              <p className={styles.blockNotice}>
                <strong>확정 차단</strong> · 오래된 근거입니다. 최신성 검토를
                완료해야 확정할 수 있습니다.
              </p>
            )}
            <fieldset className={styles.actions} aria-label="근거 검토 조치">
              <button
                disabled={
                  pendingAction !== null ||
                  selected.status !== EvidenceLinkStatus.Candidate ||
                  selected.freshness === EvidenceFreshness.Stale
                }
                onClick={() => performAction("confirm")}
                type="button"
              >
                {pendingAction === "confirm" ? "확정 중…" : "명시적으로 확정"}
              </button>
              <button
                disabled={
                  pendingAction !== null ||
                  selected.status !== EvidenceLinkStatus.Candidate
                }
                onClick={() => performAction("reject")}
                type="button"
              >
                {pendingAction === "reject" ? "거절 중…" : "후보 거절"}
              </button>
              <button
                disabled={
                  pendingAction !== null ||
                  selected.freshness !== EvidenceFreshness.Stale
                }
                onClick={() => performAction("review")}
                type="button"
              >
                {pendingAction === "review" ? "검토 중…" : "최신성 검토 완료"}
              </button>
            </fieldset>
            <p className={styles.actionHint}>
              조치 성공 후 문서별 근거 연결을 다시 조회합니다.
            </p>
          </>
        ) : (
          <p className={styles.empty}>
            {isLoading
              ? "근거를 불러오는 중입니다."
              : "선택된 근거가 없습니다."}
          </p>
        )}
      </aside>
    </div>
  );
}
