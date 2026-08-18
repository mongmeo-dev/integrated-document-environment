import { WorkspaceHeader } from "@/components/workspace-header";

import { ApprovalWorkspace } from "./approval-workspace";
import styles from "./approvals.module.css";

export default function ApprovalsPage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#approval-workspace">
        승인 흐름으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/approvals/" />
      <ApprovalWorkspace />
    </main>
  );
}
