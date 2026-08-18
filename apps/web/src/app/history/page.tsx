import { WorkspaceHeader } from "@/components/workspace-header";

import styles from "./history.module.css";
import { HistoryWorkspace } from "./history-workspace";

export default function HistoryPage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#history-workspace">
        감사 이력으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/history/" />
      <HistoryWorkspace />
    </main>
  );
}
