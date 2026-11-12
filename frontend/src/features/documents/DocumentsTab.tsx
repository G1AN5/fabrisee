import { Eye, EyeOff, FileText, FolderOpen } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { FileLinks } from "@/components/FilePreview";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjectDocuments } from "@/features/projects/api";
import { DOCUMENT_TYPE_LABELS, DOCUMENT_TYPE_ORDER } from "@/lib/constants";
import { formatDate, formatFileSize } from "@/lib/format";
import type { ProjectDocument } from "@/lib/types";
import { cn } from "@/lib/utils";

function DocumentRow({
  document,
  showVisibility,
}: {
  document: ProjectDocument;
  showVisibility: boolean;
}) {
  const details = [
    formatFileSize(document.file.size_bytes),
    document.uploaded_by ? `Uploaded by ${document.uploaded_by.full_name}` : "",
    formatDate(document.created_at),
  ].filter(Boolean);
  return (
    <li className="flex flex-col gap-3 px-5 py-3 sm:flex-row sm:items-center sm:px-6">
      <span className="flex min-w-0 flex-1 items-center gap-3">
        {document.thumbnail_url ? (
          <img
            src={document.thumbnail_url}
            alt=""
            loading="lazy"
            className="h-12 w-16 shrink-0 rounded-sm border object-cover"
          />
        ) : (
          <span
            className={cn(
              "flex h-12 w-16 shrink-0 items-center justify-center rounded-sm",
              document.file.is_pdf
                ? "bg-status-changes-bg text-status-changes"
                : "bg-muted text-slate-600",
            )}
          >
            <FileText className="size-5" aria-hidden="true" />
          </span>
        )}
        <span className="min-w-0">
          <span
            className="block truncate font-medium text-foreground"
            title={document.original_name}
          >
            {document.original_name}
          </span>
          <span className="block text-xs text-muted-foreground">{details.join(" · ")}</span>
          {showVisibility && (
            <span
              className={cn(
                "mt-1 inline-flex items-center gap-1 text-xs font-medium",
                document.visible_to_client ? "text-status-sent" : "text-status-neutral",
              )}
            >
              {document.visible_to_client ? (
                <Eye className="size-3.5" aria-hidden="true" />
              ) : (
                <EyeOff className="size-3.5" aria-hidden="true" />
              )}
              {document.visible_to_client ? "Visible to the client" : "Staff only"}
            </span>
          )}
        </span>
      </span>
      <FileLinks file={document.file} compact />
    </li>
  );
}

interface DocumentsTabProps {
  projectId: number;
  /** Staff see whether each document is visible to the client. */
  showVisibility?: boolean;
  forClient?: boolean;
}

/** The project document repository, grouped by type (read-only). */
export function DocumentsTab({
  projectId,
  showVisibility = false,
  forClient = false,
}: DocumentsTabProps) {
  const documents = useProjectDocuments(projectId);

  if (documents.isPending) {
    return (
      <Card className="p-5">
        <div aria-hidden="true" className="flex flex-col gap-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      </Card>
    );
  }
  if (documents.isError) {
    return (
      <Card>
        <ErrorState
          error={documents.error}
          what="the documents"
          onRetry={() => void documents.refetch()}
        />
      </Card>
    );
  }
  if (documents.data.length === 0) {
    return (
      <Card>
        <EmptyState
          icon={FolderOpen}
          title="No documents yet"
          description={
            forClient
              ? "Files shared with you appear here, for example reference files and turnover documents."
              : "Reference files, turnover documents, and other project files appear here."
          }
        />
      </Card>
    );
  }

  const groups = DOCUMENT_TYPE_ORDER.map((type) => ({
    type,
    items: documents.data.filter((document) => document.doc_type === type),
  })).filter((group) => group.items.length > 0);

  return (
    <div className="flex flex-col gap-4">
      {groups.map((group) => (
        <Card key={group.type} className="overflow-hidden">
          <h3 className="flex items-baseline justify-between gap-3 border-b bg-slate-50 px-5 py-2.5 text-sm font-semibold text-foreground sm:px-6">
            {DOCUMENT_TYPE_LABELS[group.type]}
            <span className="font-normal text-muted-foreground tabular-nums">
              {group.items.length}
            </span>
          </h3>
          <ul className="divide-y">
            {group.items.map((document) => (
              <DocumentRow key={document.id} document={document} showVisibility={showVisibility} />
            ))}
          </ul>
        </Card>
      ))}
    </div>
  );
}
