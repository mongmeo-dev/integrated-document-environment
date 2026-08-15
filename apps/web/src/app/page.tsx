import { SystemHealthStatus } from "@/features/system/system-health-status";

import styles from "./page.module.css";

const Icon = ({
  name,
  size = 18,
}: {
  name:
    | "archive"
    | "bell"
    | "check"
    | "chevron"
    | "clock"
    | "document"
    | "evidence"
    | "home"
    | "link"
    | "search"
    | "settings"
    | "shield"
    | "upload"
    | "users"
    | "warning";
  size?: number;
}) => {
  const paths = {
    archive: <path d="M3 6.5h18M5 6.5v13h14v-13M3 3h18v3.5H3zM9 11h6" />,
    bell: (
      <>
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
        <path d="M10 21h4" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    chevron: <path d="m9 18 6-6-6-6" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
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
    home: (
      <>
        <path d="m3 11 9-8 9 8" />
        <path d="M5 10v11h14V10M9 21v-7h6v7" />
      </>
    ),
    link: (
      <>
        <path d="M10 13a5 5 0 0 0 7.5.5l2-2a5 5 0 0 0-7-7l-1 1" />
        <path d="M14 11a5 5 0 0 0-7.5-.5l-2 2a5 5 0 0 0 7 7l1-1" />
      </>
    ),
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
      </>
    ),
    shield: (
      <>
        <path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V3M7 8l5-5 5 5" />
        <path d="M5 13v7h14v-7" />
      </>
    ),
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
        strokeWidth="1.8"
      >
        {paths[name]}
      </g>
    </svg>
  );
};

const workflowSteps = [
  { label: "변경 요청", status: "done" },
  { label: "수정안 검토", status: "done" },
  { label: "외부 편집", status: "current" },
  { label: "서식 검증", status: "upcoming" },
  { label: "단계 승인", status: "upcoming" },
];

export default function Home() {
  return (
    <div className={styles.shell}>
      <a className={styles.skipLink} href="#main-content">
        본문으로 건너뛰기
      </a>

      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <span className={styles.brandMark} aria-hidden="true">
            ND
          </span>
          <span>
            <strong>뉴다이브</strong>
            <small>Document IDE</small>
          </span>
        </div>

        <nav aria-label="주 메뉴" className={styles.navigation}>
          <a aria-current="page" className={styles.navActive} href="#dashboard">
            <Icon name="home" />
            작업 홈
          </a>
          <a href="#documents">
            <Icon name="document" />
            문서
            <span className={styles.navCount}>12</span>
          </a>
          <a href="#requests">
            <Icon name="bell" />
            변경 요청
            <span className={styles.navCount}>5</span>
          </a>
          <a href="#relations">
            <Icon name="link" />
            관계·영향
          </a>
          <a href="#evidence">
            <Icon name="evidence" />
            제품·검증 근거
            <span className={styles.navCountWarning}>3</span>
          </a>
          <a href="#approvals">
            <Icon name="users" />
            승인 흐름
          </a>
          <a href="#history">
            <Icon name="archive" />
            변경 이력
          </a>
        </nav>

        <div className={styles.sidebarFooter}>
          <a href="#settings">
            <Icon name="settings" />
            설정
          </a>
          <SystemHealthStatus />
        </div>
      </aside>

      <header className={styles.topbar}>
        <label className={styles.search}>
          <Icon name="search" />
          <span className={styles.visuallyHidden}>문서 검색</span>
          <input placeholder="문서명, 문서 번호 검색" type="search" />
          <kbd>⌘ K</kbd>
        </label>
        <div className={styles.topActions}>
          <button
            aria-label="알림 3개"
            className={styles.iconButton}
            type="button"
          >
            <Icon name="bell" />
            <span className={styles.notificationDot} />
          </button>
          <div className={styles.profile}>
            <span className={styles.avatar} aria-hidden="true">
              김
            </span>
            <span>
              <strong>김민준</strong>
              <small>품질관리팀</small>
            </span>
          </div>
        </div>
      </header>

      <main className={styles.main} id="main-content">
        <section className={styles.pageHeading} id="dashboard">
          <div>
            <p>2026년 8월 15일 토요일</p>
            <h1>안녕하세요, 김민준님</h1>
            <span>검토가 필요한 문서와 진행 중인 작업을 확인하세요.</span>
          </div>
          <a className={styles.primaryButton} href="#documents">
            <Icon name="upload" />새 문서 등록
          </a>
        </section>

        <section aria-label="업무 현황" className={styles.metricGrid}>
          <article>
            <div className={styles.metricIcon}>
              <Icon name="clock" size={20} />
            </div>
            <div>
              <p>내 검토 대기</p>
              <strong>5</strong>
              <span>오늘 마감 2건</span>
            </div>
          </article>
          <article>
            <div className={styles.metricIconBlue}>
              <Icon name="document" size={20} />
            </div>
            <div>
              <p>진행 중 문서</p>
              <strong>8</strong>
              <span>이번 주 +3건</span>
            </div>
          </article>
          <article>
            <div className={styles.metricIconAmber}>
              <Icon name="warning" size={20} />
            </div>
            <div>
              <p>재검토 필요 근거</p>
              <strong>3</strong>
              <span>오래됨 가능성</span>
            </div>
          </article>
          <article>
            <div className={styles.metricIconGreen}>
              <Icon name="shield" size={20} />
            </div>
            <div>
              <p>서식 검증 완료</p>
              <strong>14</strong>
              <span>미해결 차이 0건</span>
            </div>
          </article>
        </section>

        <div className={styles.contentGrid}>
          <section className={styles.panel} id="requests">
            <div className={styles.panelHeader}>
              <div>
                <p className={styles.eyebrow}>우선 처리</p>
                <h2>내 검토 대기</h2>
              </div>
              <a href="#documents">
                전체 보기
                <Icon name="chevron" size={16} />
              </a>
            </div>

            <div className={styles.reviewList}>
              <article className={styles.reviewItem}>
                <div className={styles.fileIconDocx}>W</div>
                <div className={styles.reviewBody}>
                  <div className={styles.reviewTitle}>
                    <div>
                      <h3>소프트웨어 요구사항 명세서</h3>
                      <p>ND-SRS-002 · DOCX · v2.4</p>
                    </div>
                    <span className={styles.badgeUrgent}>오늘 마감</span>
                  </div>
                  <ol
                    className={styles.workflow}
                    aria-label="현재 외부 편집 단계"
                  >
                    {workflowSteps.map((step, index) => (
                      <li
                        className={`${styles.workflowStep} ${styles[step.status]}`}
                        key={step.label}
                      >
                        <span>
                          {step.status === "done" ? (
                            <Icon name="check" size={12} />
                          ) : (
                            index + 1
                          )}
                        </span>
                        <small>{step.label}</small>
                      </li>
                    ))}
                  </ol>
                  <div className={styles.reviewMeta}>
                    <span>
                      <Icon name="users" size={15} /> 검토 담당: 김민준
                    </span>
                    <span>수정안 후보 2건</span>
                    <a href="#review-srs">
                      검토하기 <Icon name="chevron" size={15} />
                    </a>
                  </div>
                </div>
              </article>

              <article className={styles.reviewItem}>
                <div className={styles.fileIconPdf}>PDF</div>
                <div className={styles.reviewBody}>
                  <div className={styles.reviewTitle}>
                    <div>
                      <h3>위험관리 보고서</h3>
                      <p>ND-RMR-018 · 텍스트 PDF · v1.7</p>
                    </div>
                    <span className={styles.badgeDefault}>내일 마감</span>
                  </div>
                  <div className={styles.gateSummary}>
                    <span className={styles.gateDone}>
                      <Icon name="check" size={14} /> 자동 서식 검사 완료
                    </span>
                    <span className={styles.gatePending}>
                      <Icon name="clock" size={14} /> 시각 비교 대기
                    </span>
                  </div>
                  <div className={styles.reviewMeta}>
                    <span>
                      <Icon name="users" size={15} /> 검토 담당: 김민준
                    </span>
                    <span>관계 후보 4건</span>
                    <a href="#compare-rmr">
                      비교하기 <Icon name="chevron" size={15} />
                    </a>
                  </div>
                </div>
              </article>
            </div>
          </section>

          <aside className={styles.panel} id="approvals">
            <div className={styles.panelHeader}>
              <div>
                <p className={styles.eyebrow}>오늘의 흐름</p>
                <h2>승인 진행 현황</h2>
              </div>
              <a href="#approval-detail" aria-label="승인 진행 현황 전체 보기">
                <Icon name="chevron" size={17} />
              </a>
            </div>
            <div className={styles.approvalSummary}>
              <div className={styles.progressRing}>
                <span>
                  <strong>68%</strong>
                  <small>완료</small>
                </span>
              </div>
              <div>
                <strong>21 / 31 단계</strong>
                <p>이번 주 승인 진행률</p>
              </div>
            </div>
            <div className={styles.approvalStages}>
              <div>
                <span className={styles.stageDotDone}>
                  <Icon name="check" size={13} />
                </span>
                <div>
                  <strong>작성 검토</strong>
                  <small>박서연 · 8월 13일 완료</small>
                </div>
              </div>
              <div>
                <span className={styles.stageDotCurrent}>2</span>
                <div>
                  <strong>품질 검토</strong>
                  <small>김민준 · 진행 중</small>
                </div>
                <span className={styles.badgeActive}>현재</span>
              </div>
              <div>
                <span className={styles.stageDotUpcoming}>3</span>
                <div>
                  <strong>최종 승인</strong>
                  <small>이정우 · 대기</small>
                </div>
              </div>
            </div>
            <div className={styles.blockerNotice}>
              <Icon name="warning" size={18} />
              <div>
                <strong>승인 차단 조건 2건</strong>
                <p>미확정 후보 1건 · 시각 비교 1건</p>
              </div>
            </div>
          </aside>
        </div>

        <section className={styles.panel} id="documents">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>최근 활동</p>
              <h2>진행 중인 문서</h2>
            </div>
            <a href="#all-documents">
              모든 문서
              <Icon name="chevron" size={16} />
            </a>
          </div>
          <div className={styles.tableWrap}>
            <table>
              <thead>
                <tr>
                  <th scope="col">문서</th>
                  <th scope="col">현재 단계</th>
                  <th scope="col">담당자</th>
                  <th scope="col">서식 무결성</th>
                  <th scope="col">최근 변경</th>
                  <th scope="col">
                    <span className={styles.visuallyHidden}>열기</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <strong>사용적합성 평가 계획서</strong>
                    <small>ND-UEP-006 · DOCX</small>
                  </td>
                  <td>
                    <span className={styles.statusInProgress}>영향 검토</span>
                  </td>
                  <td>최유진</td>
                  <td>
                    <span className={styles.integrityPass}>
                      <Icon name="check" size={14} /> 차이 없음
                    </span>
                  </td>
                  <td>2시간 전</td>
                  <td>
                    <a
                      aria-label="사용적합성 평가 계획서 열기"
                      href="#document-uep"
                    >
                      <Icon name="chevron" size={17} />
                    </a>
                  </td>
                </tr>
                <tr>
                  <td>
                    <strong>소프트웨어 검증 보고서</strong>
                    <small>ND-SVR-011 · PDF</small>
                  </td>
                  <td>
                    <span className={styles.statusReview}>서식 검증</span>
                  </td>
                  <td>한지호</td>
                  <td>
                    <span className={styles.integrityWarning}>
                      <Icon name="warning" size={14} /> 차이 2건
                    </span>
                  </td>
                  <td>어제</td>
                  <td>
                    <a
                      aria-label="소프트웨어 검증 보고서 열기"
                      href="#document-svr"
                    >
                      <Icon name="chevron" size={17} />
                    </a>
                  </td>
                </tr>
                <tr>
                  <td>
                    <strong>사이버보안 위험분석서</strong>
                    <small>ND-CRA-004 · DOCX</small>
                  </td>
                  <td>
                    <span className={styles.statusApproval}>단계 승인</span>
                  </td>
                  <td>김민준</td>
                  <td>
                    <span className={styles.integrityPass}>
                      <Icon name="check" size={14} /> 검증 완료
                    </span>
                  </td>
                  <td>8월 13일</td>
                  <td>
                    <a
                      aria-label="사이버보안 위험분석서 열기"
                      href="#document-cra"
                    >
                      <Icon name="chevron" size={17} />
                    </a>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
