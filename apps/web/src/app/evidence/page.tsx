import { WorkspaceHeader } from "@/components/workspace-header";

import styles from "./evidence.module.css";
import { EvidenceWorkspace } from "./evidence-workspace";

export default function EvidencePage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#evidence-list">
        근거 목록으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/evidence/" />
      <EvidenceWorkspace />
    </main>
  );
}
