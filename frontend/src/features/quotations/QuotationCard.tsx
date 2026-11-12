import { FilePreview, FileRow } from "@/components/FilePreview";
import { Money } from "@/components/Money";
import { RelativeTime } from "@/components/RelativeTime";
import { StatusBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/format";
import type { Quotation } from "@/lib/types";
import { cn } from "@/lib/utils";

/** `Recorded by A. Villanueva on behalf of M. Bautista (phone)`, or null. */
function onBehalfText(quotation: Quotation): string | null {
  if (!quotation.decided_on_behalf || !quotation.decided_by) return null;
  const recorder = quotation.recorded_by?.short_name ?? "staff";
  const channel = quotation.decision_channel_label
    ? ` (${quotation.decision_channel_label.toLowerCase()})`
    : "";
  return `Recorded by ${recorder} on behalf of ${quotation.decided_by.short_name}${channel}`;
}

function Decision({ quotation, forClient }: { quotation: Quotation; forClient: boolean }) {
  const behalf = onBehalfText(quotation);
  const who = quotation.decided_by?.full_name ?? "the client";

  if (quotation.decision === "accepted" && quotation.decided_at) {
    return (
      <div className="rounded-md border border-status-approved-border bg-status-approved-bg px-3 py-2 text-status-approved">
        <p className="font-medium">
          Accepted by {who} on {formatDate(quotation.decided_at)}
        </p>
        {behalf && <p className="text-xs">{behalf}</p>}
      </div>
    );
  }
  if (quotation.decision === "returned" && quotation.decided_at) {
    return (
      <div className="rounded-md border border-status-changes-border bg-status-changes-bg px-3 py-2">
        <p className="font-medium text-status-changes">
          Returned with comments by {who} on {formatDate(quotation.decided_at)}
        </p>
        {behalf && <p className="text-xs text-status-changes">{behalf}</p>}
        {quotation.client_comment && (
          <blockquote className="mt-2 border-l-2 border-status-changes-border pl-3 text-foreground">
            {quotation.client_comment}
          </blockquote>
        )}
      </div>
    );
  }
  if (quotation.status === "sent" && quotation.sent_at) {
    return (
      <p className="rounded-md border border-status-pending-border bg-status-pending-bg px-3 py-2 text-status-pending">
        {forClient ? "Waiting for a decision" : "Waiting for the client's decision"}, sent{" "}
        <RelativeTime value={quotation.sent_at} />
        {quotation.last_reminded_at && (
          <>
            {" "}
            · reminder sent <RelativeTime value={quotation.last_reminded_at} />
          </>
        )}
      </p>
    );
  }
  if (quotation.status === "draft") {
    return (
      <p className="rounded-md border border-status-neutral-border bg-status-neutral-bg px-3 py-2 text-status-neutral">
        Draft. Not sent to the client yet.
      </p>
    );
  }
  if (quotation.status === "superseded") {
    return (
      <p className="rounded-md border border-status-neutral-border bg-status-neutral-bg px-3 py-2 text-status-neutral">
        Replaced by a newer version before a decision.
      </p>
    );
  }
  return null;
}

interface QuotationCardProps {
  quotation: Quotation;
  /** Wording for the client portal ("your decision") instead of the staff workspace. */
  forClient?: boolean;
  /** Show the PDF itself where the browser can, not only the links to it. */
  preview?: boolean;
  className?: string;
}

/** One quotation version: amount, status, who prepared and decided it, and the PDF. */
export function QuotationCard({
  quotation,
  forClient = false,
  preview = false,
  className,
}: QuotationCardProps) {
  return (
    <article
      className={cn("flex flex-col gap-4 rounded-lg border bg-card p-5 shadow-xs", className)}
    >
      <header className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <h3 className="text-lg font-semibold text-foreground">Quotation {quotation.label}</h3>
          <StatusBadge status={quotation.status} />
        </div>
        <Money amount={quotation.amount} className="text-xl font-semibold text-foreground" />
      </header>

      <dl className="grid grid-cols-1 gap-x-8 gap-y-2 text-sm sm:grid-cols-3">
        {quotation.prepared_by && (
          <div>
            <dt className="text-xs text-muted-foreground">Prepared by</dt>
            <dd className="text-foreground">{quotation.prepared_by.full_name}</dd>
          </div>
        )}
        <div>
          <dt className="text-xs text-muted-foreground">
            {quotation.sent_at ? "Sent" : "Created"}
          </dt>
          <dd className="text-foreground tabular-nums">
            {formatDate(quotation.sent_at ?? quotation.created_at)}
          </dd>
        </div>
      </dl>

      <Decision quotation={quotation} forClient={forClient} />

      {quotation.notes && (
        <div>
          <h4 className="text-xs font-medium text-muted-foreground">Notes</h4>
          <p className="mt-1 whitespace-pre-line text-foreground">{quotation.notes}</p>
        </div>
      )}

      {preview ? (
        <FilePreview file={quotation.file} alt={`Quotation ${quotation.label}`} />
      ) : (
        <FileRow file={quotation.file} />
      )}
    </article>
  );
}
