import { WorkspaceHeader } from "@/components/workspace-header";

import styles from "./formatting.module.css";
import { FormattingWorkspace } from "./formatting-workspace";

export default function FormattingPage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#formatting-workspace">
        서식 비교 작업공간으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/formatting/" />
      <FormattingWorkspace />
    </main>
  );
}
