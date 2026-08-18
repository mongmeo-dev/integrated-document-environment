import { WorkspaceHeader } from "@/components/workspace-header";
import DocumentRegistrationForm from "./document-registration-form";
import styles from "./new-document.module.css";

export default function NewDocumentPage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#registration-form">
        등록 양식으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/documents/new/" />

      <div className={styles.workspace}>
        <aside className={styles.sidebar} aria-label="등록 단계">
          <p className={styles.eyebrow}>문서 등록 준비</p>
          <strong>SaMD Core v2.4</strong>
          <ol>
            <li className={styles.activeStep}>
              <span>1</span>
              <div>
                <strong>원본 선택</strong>
                <small>DOCX 또는 PDF</small>
              </div>
            </li>
            <li>
              <span>2</span>
              <div>
                <strong>등록 검토</strong>
                <small>API 연결 대기</small>
              </div>
            </li>
          </ol>
          <section className={styles.boundary}>
            <span>지원 경계</span>
            <p>
              DOCX와 PDF만 선택할 수 있습니다. 스캔 PDF는 분석 전용으로
              제공됩니다.
            </p>
          </section>
        </aside>
        <section className={styles.content} id="registration-form">
          <div className={styles.breadcrumb}>
            문서 구조 / 전체 문서 / 등록 준비
          </div>
          <h1>문서 등록 준비</h1>
          <p className={styles.lead}>
            원본을 선택하고 등록 전에 파일 정보를 검토합니다.
          </p>
          <DocumentRegistrationForm />
        </section>
        <aside className={styles.reviewPanel} aria-label="등록 안내">
          <span>등록 전 확인</span>
          <h2>원본 기준</h2>
          <ul>
            <li>빈 파일은 등록할 수 없습니다.</li>
            <li>파일 유형은 확장자와 MIME 유형으로 확인합니다.</li>
            <li>등록 API는 아직 연결되지 않았습니다.</li>
          </ul>
          <div className={styles.scannedPdf}>
            <strong>스캔 PDF</strong>
            <p>
              이미지 기반 PDF는 분석 전용이며 편집 가능한 문서로 전환되지
              않습니다.
            </p>
          </div>
        </aside>
      </div>
    </main>
  );
}
