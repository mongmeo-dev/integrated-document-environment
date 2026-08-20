import DocumentValidationStatus from "@/app/documents/validation/document-validation-status";
import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";

export default async function DocumentValidationPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell currentSection="validation" documentId={documentId}>
      <DocumentValidationStatus documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
