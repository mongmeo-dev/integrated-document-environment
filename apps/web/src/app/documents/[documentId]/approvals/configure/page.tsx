import { ApprovalConfigurator } from "@/app/approvals/approval-configurator";
import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";

export default async function ApprovalConfigurationPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell currentSection="approvals" documentId={documentId}>
      <ApprovalConfigurator documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
