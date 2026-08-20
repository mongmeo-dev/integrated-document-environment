import { DocumentWorkspaceShell } from "@/components/document-workspace-shell";
import { ConversionReview } from "@/features/document-workbench/conversion-review";

export default async function ImportReviewPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return (
    <DocumentWorkspaceShell
      currentSection="import-review"
      documentId={documentId}
    >
      <ConversionReview documentId={documentId} />
    </DocumentWorkspaceShell>
  );
}
