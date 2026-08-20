import { WorkspaceHeader } from "@/components/workspace-header";
import DocumentRegistrationForm from "./document-registration-form";
import styles from "./new-document.module.css";

export default function NewDocumentPage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#registration-form">
        등록 양식으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/documents/" />

      <section className={styles.workspace}>
        <div className={styles.content}>
          <nav aria-label="경로" className={styles.breadcrumb}>
            <a href="/documents/">문서</a>
            <span aria-hidden="true">/</span>
            <span aria-current="page">원본 등록</span>
          </nav>
          <header className={styles.introduction}>
            <p className={styles.eyebrow}>원본 문서 등록</p>
            <h1>원본을 등록하고 검증을 시작하세요</h1>
            <p>
              원본 파일은 변경하지 않고 보관합니다. 등록이 완료되면 파일 검증
              화면으로 바로 이동합니다.
            </p>
          </header>

          <ol aria-label="문서 등록 절차" className={styles.steps}>
            <li className={styles.currentStep}>
              <span aria-hidden="true">1</span>
              <div>
                <strong>원본 선택</strong>
                <p>LaTeX 정본을 선택하거나 DOCX/PDF 보조 입력을 등록합니다.</p>
              </div>
            </li>
            <li>
              <span aria-hidden="true">2</span>
              <div>
                <strong>지원 경계 확인</strong>
                <p>파일 유형과 처리 가능한 범위를 확인합니다.</p>
              </div>
            </li>
            <li>
              <span aria-hidden="true">3</span>
              <div>
                <strong>등록 후 자동 검증</strong>
                <p>등록된 원본의 구조와 내용을 검증합니다.</p>
              </div>
            </li>
          </ol>

          <section
            aria-labelledby="support-boundary-title"
            className={styles.boundary}
          >
            <div>
              <p className={styles.eyebrow}>지원 경계</p>
              <h2 id="support-boundary-title">파일 유형별 처리 범위</h2>
            </div>
            <dl>
              <div>
                <dt>LaTeX</dt>
                <dd>
                  `.tex` 원본 또는 프로젝트 `.zip`을 정본으로 등록하고 Web에서
                  편집·컴파일합니다.
                </dd>
              </div>
              <div>
                <dt>DOCX</dt>
                <dd>
                  불변 가져오기 원본으로 보존하고 LaTeX로 자동 변환한 뒤 사람이
                  변환 결과를 검토합니다.
                </dd>
              </div>
              <div>
                <dt>PDF</dt>
                <dd>
                  텍스트 추출·OCR과 분석을 지원하지만 정본으로 편집하지
                  않습니다.
                </dd>
              </div>
            </dl>
          </section>

          <section className={styles.registration} id="registration-form">
            <DocumentRegistrationForm />
          </section>
        </div>
      </section>
    </main>
  );
}
