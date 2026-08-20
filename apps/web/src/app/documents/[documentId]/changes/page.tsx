import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";

import { ChangeRequestWorkspace } from "../../nd-srs-002/changes/change-request-workspace";

export default async function ChangeRequestsPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell currentSection="changes" documentId={documentId}>
      <ChangeRequestWorkspace documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
