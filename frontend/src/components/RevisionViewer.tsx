import { Lock } from "lucide-react";
import type { ReactNode } from "react";

import { FilePreview, FileRow } from "@/components/FilePreview";
import { RelativeTime } from "@/components/RelativeTime";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/format";
import type { Revision } from "@/lib/types";
import { cn } from "@/lib/utils";

interface RevisionViewerProps {
  revision: Revision;
  /** The approvals panel, shown under the design. */
  children?: ReactNode;
  className?: string;
}

/**
 * One design revision: the render shown large, the uploader's notes, the spec sheet, and
 * a lock notice once all designated approvers approved it.
 */
export function RevisionViewer({ revision, children, className }: RevisionViewerProps) {
  return (
    <article className={cn("flex min-w-0 flex-col gap-4", className)}>
      <header className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <h3 className="text-lg font-semibold text-foreground">Design {revision.label}</h3>
          <StatusBadge status={revision.is_locked ? "locked" : revision.status} />
        </div>
        <p className="text-xs text-muted-foreground">
          {revision.uploaded_by ? `Uploaded by ${revision.uploaded_by.full_name} ` : "Uploaded "}
          <RelativeTime value={revision.uploaded_at} />
        </p>
      </header>

      {revision.is_locked && revision.locked_at && (
        <p className="flex items-start gap-2 rounded-md border border-status-approved-border bg-status-approved-bg px-3 py-2 text-status-approved">
          <Lock className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>
            Approved by all designated approvers on {formatDate(revision.locked_at)}. This is the
            approved design; it can no longer be changed.
          </span>
        </p>
      )}

      <FilePreview file={revision.render} alt={revision.alt_text} />

      {revision.notes && (
        <div>
          <h4 className="text-xs font-medium text-muted-foreground">Notes from the designer</h4>
          <p className="mt-1 whitespace-pre-line text-foreground">{revision.notes}</p>
        </div>
      )}

      {revision.spec_sheet && <FileRow file={revision.spec_sheet} label="Spec sheet" />}

      {children}
    </article>
  );
}
