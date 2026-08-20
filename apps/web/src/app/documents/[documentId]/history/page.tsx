import { HistoryWorkspace } from "@/app/history/history-workspace";
import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";

export default async function DocumentHistoryPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell currentSection="history" documentId={documentId}>
      <HistoryWorkspace documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
