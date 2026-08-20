import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";
import { DocumentWorkbench } from "@/features/document-workbench/document-workbench";

export default async function DocumentWorkbenchPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell currentSection="workbench" documentId={documentId}>
      <DocumentWorkbench documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
