import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";

import { EvidenceWorkspace } from "../../../evidence/evidence-workspace";

export default async function DocumentEvidencePage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell currentSection="evidence" documentId={documentId}>
      <EvidenceWorkspace documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
