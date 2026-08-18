import { WorkspaceHeader } from "@/components/workspace-header";

import styles from "./completion.module.css";
import { CompletionWorkspace } from "./completion-workspace";

export default function CompletionPage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#completion-workspace">
        완료 게이트로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/completion/" />
      <CompletionWorkspace />
    </main>
  );
}
