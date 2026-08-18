import { WorkspaceHeader } from "@/components/workspace-header";

import { ImpactWorkspace } from "./impact-workspace";
import styles from "./relations.module.css";

export default function RelationsPage() {
  return (
    <main className={styles.app}>
      <a className={styles.skipLink} href="#relationship-list">
        관계 목록으로 건너뛰기
      </a>
      <WorkspaceHeader currentPath="/relations/" />
      <ImpactWorkspace />
    </main>
  );
}
