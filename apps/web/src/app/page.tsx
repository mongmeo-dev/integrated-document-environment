import { SystemHealthStatus } from "@/features/system/system-health-status";

import styles from "./page.module.css";

type IconName =
  | "branch"
  | "check"
  | "chevron"
  | "code"
  | "document"
  | "evidence"
  | "folder"
  | "history"
  | "link"
  | "refresh"
  | "search"
  | "shield"
  | "split"
  | "users"
  | "warning"
  | "workflow";

function Icon({ name, size = 16 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, React.ReactNode> = {
    branch: (
      <>
        <circle cx="6" cy="5" r="2" />
        <circle cx="18" cy="6" r="2" />
        <circle cx="6" cy="19" r="2" />
        <path d="M6 7v10M8 10h4a6 6 0 0 0 6-2" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    chevron: <path d="m9 18 6-6-6-6" />,
    code: <path d="m8 9-3 3 3 3M16 9l3 3-3 3M14 5l-4 14" />,
    document: (
      <>
        <path d="M6 2h8l4 4v16H6z" />
        <path d="M14 2v5h5M9 12h6M9 16h6" />
      </>
    ),
    evidence: (
      <>
        <path d="M5 3h14v18H5zM9 3V1h6v2" />
        <path d="m8 12 2.5 2.5L16 9" />
      </>
    ),
    folder: <path d="M3 5h7l2 2h9v12H3z" />,
    history: (
      <>
        <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
        <path d="M3 3v5h5M12 7v5l3 2" />
      </>
    ),
    link: (
      <>
        <path d="M10 13a5 5 0 0 0 7.5.5l2-2a5 5 0 0 0-7-7l-1 1" />
        <path d="M14 11a5 5 0 0 0-7.5-.5l-2 2a5 5 0 0 0 7 7l1-1" />
      </>
    ),
    refresh: (
      <>
        <path d="M20 7v5h-5M4 17v-5h5" />
        <path d="M6.1 8a7 7 0 0 1 11.4-2.2L20 8M4 16l2.5 2.2A7 7 0 0 0 17.9 16" />
      </>
    ),
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),
    shield: (
      <>
        <path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    split: <path d="M4 4h16v16H4zM12 4v16" />,
    users: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3 20v-2a6 6 0 0 1 12 0v2M16 5a3 3 0 0 1 0 6M17 14a6 6 0 0 1 4 6" />
      </>
    ),
    warning: (
      <>
        <path d="M12 3 2 21h20L12 3Z" />
        <path d="M12 9v5M12 18h.01" />
      </>
    ),
    workflow: (
      <>
        <circle cx="6" cy="6" r="2" />
        <circle cx="18" cy="18" r="2" />
        <path d="M8 6h5a5 5 0 0 1 5 5v5M16 18h-5a5 5 0 0 1-5-5V8" />
      </>
    ),
  };

  return (
    <svg
      aria-hidden="true"
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
    >
      <g
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
      >
        {paths[name]}
      </g>
    </svg>
  );
}

const workflow = [
  { label: "변경 요청", state: "done" },
  { label: "수정안 검토", state: "done" },
  { label: "외부 편집", state: "active" },
  { label: "서식 검증", state: "idle" },
  { label: "단계 승인", state: "idle" },
];

export default function Home() {
  return (
    <div className={styles.app}>
      <a className={styles.skipLink} href="#document-editor">
        문서 편집 영역으로 건너뛰기
      </a>

      <header className={styles.header}>
        <a className={styles.brand} href="#workspace">
          <span className={styles.brandMark}>ND</span>
          <span>
            <strong>Document Workspace</strong>
            <small>GMP Development</small>
          </span>
        </a>

        <nav aria-label="주 메뉴" className={styles.primaryNav}>
          <a aria-current="page" href="#documents">
            문서
          </a>
          <a href="#relations">관계·영향</a>
          <a href="#evidence">제품·검증 근거</a>
          <a href="#approvals">승인 흐름</a>
          <a href="#history">변경 이력</a>
        </nav>

        <div className={styles.headerTools}>
          <label className={styles.search}>
            <Icon name="search" size={14} />
            <span className={styles.visuallyHidden}>문서 또는 명령 검색</span>
            <input placeholder="문서 또는 명령 검색" type="search" />
            <kbd>⌘ K</kbd>
          </label>
          <span className={styles.userBadge}>KM</span>
        </div>
      </header>

      <div className={styles.workspace} id="workspace">
        <aside className={styles.projectPanel} id="documents">
          <div className={styles.projectHeading}>
            <div>
              <span>현재 작업공간</span>
              <strong>SaMD Core v2.4</strong>
            </div>
            <a aria-label="작업공간 새로고침" href="#refresh">
              <Icon name="refresh" size={14} />
            </a>
          </div>

          <div className={styles.branchInfo}>
            <Icon name="branch" size={14} />
            <span>change/CR-024</span>
            <b>4 changes</b>
          </div>

          <div className={styles.panelSection}>
            <div className={styles.sectionLabel}>
              <span>문서 구조</span>
              <a href="#new-document">+ 추가</a>
            </div>
            <div className={styles.tree}>
              <div className={styles.folderRow}>
                <span>⌄</span>
                <Icon name="folder" size={15} />
                <strong>제품 개발</strong>
              </div>
              <a className={styles.fileActive} href="#document-editor">
                <span className={styles.fileTypeWord}>W</span>
                <span>
                  <strong>SRS 요구사항 명세서</strong>
                  <small>ND-SRS-002 · v2.4</small>
                </span>
                <b>수정</b>
              </a>
              <a className={styles.fileRow} href="#sds">
                <span className={styles.fileTypeWord}>W</span>
                <span>
                  <strong>SDS 설계 명세서</strong>
                  <small>ND-SDS-004 · v1.8</small>
                </span>
                <i>2</i>
              </a>
              <a className={styles.fileRow} href="#trace">
                <span className={styles.fileTypeSheet}>X</span>
                <span>
                  <strong>추적성 매트릭스</strong>
                  <small>ND-TRM-003 · v2.1</small>
                </span>
              </a>
              <div className={styles.folderRow}>
                <span>›</span>
                <Icon name="folder" size={15} />
                <strong>위험 관리</strong>
                <i>3</i>
              </div>
              <div className={styles.folderRow}>
                <span>›</span>
                <Icon name="folder" size={15} />
                <strong>소프트웨어 검증</strong>
              </div>
              <div className={styles.folderRow}>
                <span>›</span>
                <Icon name="folder" size={15} />
                <strong>사용적합성</strong>
              </div>
            </div>
          </div>

          <div className={styles.panelSection}>
            <div className={styles.sectionLabel}>
              <span>현재 문서 목차</span>
            </div>
            <nav aria-label="현재 문서 목차" className={styles.outline}>
              <a href="#section-1">
                <span>01</span> 목적
              </a>
              <a href="#section-2">
                <span>02</span> 적용 범위
              </a>
              <a aria-current="location" href="#section-3">
                <span>03</span> 소프트웨어 요구사항
              </a>
              <a href="#section-4">
                <span>04</span> 인터페이스 요구사항
              </a>
            </nav>
          </div>

          <div className={styles.myQueue}>
            <div className={styles.sectionLabel}>
              <span>내 작업</span>
              <b>3</b>
            </div>
            <a href="#review">
              <span className={styles.queueDotBlue} />
              검토 대기
              <b>2</b>
            </a>
            <a href="#stale">
              <span className={styles.queueDotAmber} />
              근거 재검토
              <b>1</b>
            </a>
          </div>
        </aside>

        <main className={styles.editor} id="document-editor">
          <div className={styles.tabs}>
            <a className={styles.activeTab} href="#document">
              <span className={styles.wordGlyph}>W</span>
              SRS 요구사항 명세서
              <span aria-hidden="true" className={styles.modifiedDot} />
              <span className={styles.visuallyHidden}>수정됨</span>
            </a>
            <a href="#impact-map">
              <Icon name="branch" size={14} />
              영향 맵
            </a>
          </div>

          <section className={styles.documentHeader}>
            <div>
              <div className={styles.breadcrumbs}>
                <span>제품 개발</span>
                <Icon name="chevron" size={11} />
                <span>ND-SRS-002</span>
                <Icon name="chevron" size={11} />
                <strong>3.2 데이터 무결성</strong>
              </div>
              <div className={styles.titleRow}>
                <span className={styles.requestId}>CR-024</span>
                <h1>감사 로그 보존 기간 변경</h1>
                <span className={styles.reviewState}>검토 중</span>
              </div>
              <p>요청자 박서연 · 18분 전 · 원본 v2.4</p>
            </div>
            <div className={styles.actions}>
              <a className={styles.rejectAction} href="#reject">
                반려
              </a>
              <a className={styles.acceptAction} href="#accept">
                <Icon name="check" size={14} />
                수정안 수락
              </a>
            </div>
          </section>

          <ol aria-label="문서 변경 진행 단계" className={styles.workflow}>
            {workflow.map((step, index) => (
              <li className={styles[step.state]} key={step.label}>
                <span>
                  {step.state === "done" ? (
                    <Icon name="check" size={11} />
                  ) : (
                    index + 1
                  )}
                </span>
                <small>{step.label}</small>
              </li>
            ))}
          </ol>

          <section className={styles.compareToolbar}>
            <div>
              <strong>원본과 수정안 비교</strong>
              <span>문단 기준</span>
            </div>
            <div>
              <span className={styles.formatPass}>
                <Icon name="shield" size={13} /> 자동 서식 검사 통과
              </span>
              <a href="#visual-check">
                <Icon name="split" size={13} /> 시각 비교
              </a>
            </div>
          </section>

          <section className={styles.diffEditor} id="document">
            <article className={styles.diffPane}>
              <div className={styles.diffPaneTitle}>
                <span>
                  원본 <small>v2.4</small>
                </span>
                <b>읽기 전용</b>
              </div>
              <div className={styles.documentPage}>
                <div className={styles.documentMeta}>
                  <span>ND-SRS-002</span>
                  <span>Software Requirements Specification</span>
                </div>
                <h2>3.2 데이터 무결성</h2>
                <p className={styles.clause}>
                  3.2.1 시스템은 모든 사용자 활동에 대한 감사 로그를 생성해야
                  한다.
                </p>
                <div className={styles.removedLine}>
                  <span>42</span>
                  <p>
                    감사 로그는 생성일로부터 <mark>1년간</mark> 보존되어야 하며,
                    관리자 권한을 가진 사용자만 조회할 수 있어야 한다.
                  </p>
                </div>
                <p className={styles.clause}>
                  3.2.3 감사 로그에는 사용자, 시각, 대상 및 수행 작업이
                  포함되어야 한다.
                </p>
                <table>
                  <tbody>
                    <tr>
                      <th>요구사항 ID</th>
                      <td>SRS-DI-014</td>
                    </tr>
                    <tr>
                      <th>중요도</th>
                      <td>High</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>

            <article className={styles.diffPane}>
              <div className={styles.diffPaneTitle}>
                <span>
                  수정안 <small>CR-024</small>
                </span>
                <b className={styles.safeLabel}>
                  <Icon name="shield" size={11} /> 서식 유지
                </b>
              </div>
              <div className={styles.documentPage}>
                <div className={styles.documentMeta}>
                  <span>ND-SRS-002</span>
                  <span>Software Requirements Specification</span>
                </div>
                <h2>3.2 데이터 무결성</h2>
                <p className={styles.clause}>
                  3.2.1 시스템은 모든 사용자 활동에 대한 감사 로그를 생성해야
                  한다.
                </p>
                <div className={styles.addedLine}>
                  <span>42</span>
                  <p>
                    감사 로그는 생성일로부터 <mark>3년간</mark> 보존되어야 하며,
                    관리자 권한을 가진 사용자만 조회할 수 있어야 한다.
                  </p>
                </div>
                <p className={styles.clause}>
                  3.2.3 감사 로그에는 사용자, 시각, 대상 및 수행 작업이
                  포함되어야 한다.
                </p>
                <table>
                  <tbody>
                    <tr>
                      <th>요구사항 ID</th>
                      <td>SRS-DI-014</td>
                    </tr>
                    <tr>
                      <th>중요도</th>
                      <td>High</td>
                    </tr>
                  </tbody>
                </table>
                <div className={styles.changeReason}>
                  <Icon name="link" size={14} />
                  <span>
                    <strong>변경 근거</strong>
                    ISMS-P 보존 정책 및 SOP-QA-008 개정 반영
                  </span>
                </div>
              </div>
            </article>
          </section>

          <footer className={styles.editorFooter}>
            <span>
              <Icon name="branch" size={13} /> change/CR-024
            </span>
            <span>DOCX · 42쪽</span>
            <SystemHealthStatus />
          </footer>
        </main>

        <aside className={styles.contextPanel} id="relations">
          <div className={styles.contextTabs}>
            <a aria-current="page" href="#impact">
              영향 <b>4</b>
            </a>
            <a href="#evidence">근거 3</a>
            <a href="#comments">의견 2</a>
          </div>

          <section className={styles.contextSection} id="impact">
            <div className={styles.contextHeading}>
              <div>
                <span>변경 컨텍스트</span>
                <h2>영향 후보</h2>
              </div>
              <a aria-label="영향 후보 새로고침" href="#refresh-impact">
                <Icon name="refresh" size={14} />
              </a>
            </div>
            <div className={styles.candidateProgress}>
              <span>0 / 4 확정</span>
              <div>
                <span />
              </div>
            </div>

            <article className={styles.candidate}>
              <div className={styles.candidateHeader}>
                <span className={styles.candidateIcon}>
                  <Icon name="document" size={14} />
                </span>
                <div>
                  <strong>SDS 설계 명세서</strong>
                  <small>§ 4.3 AuditLogService</small>
                </div>
                <b className={styles.high}>높음</b>
              </div>
              <p>보존 정책 구성값과 정리 작업 주기 변경 필요</p>
              <code>retention_days: 365 → 1095</code>
              <div className={styles.candidateActions}>
                <a href="#reject-sds">거절</a>
                <a href="#confirm-sds">확정</a>
              </div>
            </article>

            <article className={styles.candidate}>
              <div className={styles.candidateHeader}>
                <span className={styles.candidateIconCode}>
                  <Icon name="code" size={14} />
                </span>
                <div>
                  <strong>audit_log.py</strong>
                  <small>apps/api/services · L84</small>
                </div>
                <b className={styles.medium}>중간</b>
              </div>
              <p>환경 변수 기본 보존 기간과 문서 값 불일치</p>
              <code>AUDIT_RETENTION_DAYS</code>
              <div className={styles.candidateActions}>
                <a href="#reject-code">거절</a>
                <a href="#confirm-code">확정</a>
              </div>
            </article>

            <article className={styles.staleCandidate}>
              <div className={styles.candidateHeader}>
                <span className={styles.candidateIconWarning}>
                  <Icon name="warning" size={14} />
                </span>
                <div>
                  <strong>TC-DI-022</strong>
                  <small>감사 로그 보존 검증</small>
                </div>
                <b>재검토</b>
              </div>
              <p>요구사항 변경으로 테스트 근거 재실행 필요</p>
              <a className={styles.openLink} href="#test-evidence">
                테스트 근거 열기 <Icon name="chevron" size={12} />
              </a>
            </article>
          </section>

          <section className={styles.gateSection} id="approvals">
            <div className={styles.gateHeading}>
              <span>
                <Icon name="workflow" size={15} /> 승인 준비 상태
              </span>
              <b>2개 차단</b>
            </div>
            <div className={styles.gateItem}>
              <span className={styles.gateError}>!</span>
              <div>
                <strong>미확정 후보 4건</strong>
                <small>모든 후보를 확정 또는 거절하세요.</small>
              </div>
            </div>
            <div className={styles.gateItem}>
              <span className={styles.gateWarning}>!</span>
              <div>
                <strong>오래된 근거 1건</strong>
                <small>테스트 근거의 최신성을 검토하세요.</small>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
