import { Download, Eye, Lock, TriangleAlert } from "lucide-react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/format";
import type { Revision } from "@/lib/types";

interface ApprovedDesignCardProps {
  revision: Revision;
  /** The address of the design revisions tab, to view the approved revision. */
  viewHref: string;
  /** PR8: the design was reopened; production waits for a new approved revision. */
  reopened?: boolean;
}

/**
 * The approved design of a project: the revision that all designated approvers approved
 * and that is locked. Shown at the top of the project so nobody has to search for it.
 */
export function ApprovedDesignCard({
  revision,
  viewHref,
  reopened = false,
}: ApprovedDesignCardProps) {
  return (
    <section
      aria-labelledby="approved-design-heading"
      className="flex flex-col gap-4 rounded-lg border border-status-approved-border bg-card p-4 shadow-xs sm:flex-row sm:items-center sm:p-5"
    >
      {revision.thumbnail_url ? (
        <img
          src={revision.thumbnail_url}
          alt={revision.alt_text}
          className="design-canvas h-28 w-full shrink-0 rounded-md border object-cover sm:w-44"
        />
      ) : (
        <span className="flex h-28 w-full shrink-0 items-center justify-center rounded-md border bg-status-approved-bg text-status-approved sm:w-44">
          <Lock className="size-6" aria-hidden="true" />
        </span>
      )}
      <div className="min-w-0 flex-1">
        <h2
          id="approved-design-heading"
          className="flex items-center gap-2 text-base font-semibold text-foreground"
        >
          <Lock className="size-4 text-status-approved" aria-hidden="true" />
          Approved design
          <span className="rounded-full bg-status-approved-bg px-2 py-0.5 text-sm font-semibold text-status-approved">
            {revision.label}
          </span>
        </h2>
        <p className="mt-1 text-muted-foreground">
          Approved by all designated approvers
          {revision.locked_at ? ` on ${formatDate(revision.locked_at)}` : ""}. Locked: it can no
          longer be changed.
        </p>
        {reopened && (
          <p className="mt-2 flex items-start gap-2 text-status-pending">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <span>
              The design was reopened for a change. Production waits until a new revision is
              approved.
            </span>
          </p>
        )}
      </div>
      <div className="flex shrink-0 flex-wrap gap-2 sm:flex-col sm:items-stretch">
        <Button asChild variant="outline" size="sm">
          <Link to={viewHref}>
            <Eye aria-hidden="true" />
            View design
          </Link>
        </Button>
        <Button asChild variant="outline" size="sm">
          <a href={revision.render.url} download={revision.render.name}>
            <Download aria-hidden="true" />
            Render
            <span className="sr-only"> of the approved design, download</span>
          </a>
        </Button>
        {revision.spec_sheet && (
          <Button asChild variant="outline" size="sm">
            <a href={revision.spec_sheet.url} download={revision.spec_sheet.name}>
              <Download aria-hidden="true" />
              Spec sheet
              <span className="sr-only"> of the approved design, download</span>
            </a>
          </Button>
        )}
      </div>
    </section>
  );
}
