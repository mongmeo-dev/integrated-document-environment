import { ApprovalWorkspace } from "@/app/approvals/approval-workspace";
import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";

export default async function DocumentApprovalsPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell currentSection="approvals" documentId={documentId}>
      <ApprovalWorkspace documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
