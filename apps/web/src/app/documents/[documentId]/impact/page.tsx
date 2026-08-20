import { ImpactWorkspace } from "@/app/relations/impact-workspace";
import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";

export default async function DocumentImpactPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell currentSection="impact" documentId={documentId}>
      <ImpactWorkspace documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
