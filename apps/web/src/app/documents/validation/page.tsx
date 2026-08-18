import { WorkspaceHeader } from "@/components/workspace-header";

import DocumentValidationStatus from "./document-validation-status";
import styles from "./validation.module.css";

export default function DocumentValidationPage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#validation-result">
        검증 결과로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/documents/validation" />
      <DocumentValidationStatus />
    </main>
  );
}
