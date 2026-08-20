import { CompletionWorkspace } from "@/app/completion/completion-workspace";
import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";

export default async function DocumentCompletionPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell currentSection="completion" documentId={documentId}>
      <CompletionWorkspace documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
