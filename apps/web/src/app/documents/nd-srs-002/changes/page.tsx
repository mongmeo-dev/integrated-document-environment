import { WorkspaceHeader } from "@/components/workspace-header";

import { ChangeRequestWorkspace } from "./change-request-workspace";
import styles from "./changes.module.css";

export default function ChangeRequestsPage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#change-requests">
        변경 요청 목록으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/documents/nd-srs-002/changes/" />
      <ChangeRequestWorkspace />
    </main>
  );
}
