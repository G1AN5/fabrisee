import { Info, PenTool } from "lucide-react";
import { useSearchParams } from "react-router";

import { ApprovalPanel } from "@/components/ApprovalPanel";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { RevisionViewer } from "@/components/RevisionViewer";
import { StatusBadge } from "@/components/StatusBadge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjectRevisions } from "@/features/projects/api";
import { useCurrentUser } from "@/lib/auth";
import { formatShortDate } from "@/lib/format";
import type { Revision } from "@/lib/types";
import { cn } from "@/lib/utils";

interface RevisionsTabProps {
  projectId: number;
  /** Wording and hints for the client portal instead of the staff workspace. */
  forClient?: boolean;
  /** The signed-in user is a designated approver of this project. */
  isApprover?: boolean;
}

function RevisionList({
  revisions,
  selected,
  onSelect,
}: {
  revisions: Revision[];
  selected: Revision;
  onSelect: (revision: Revision) => void;
}) {
  return (
    <nav aria-label="Design revisions">
      <ul className="flex gap-2 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible lg:pb-0">
        {revisions.map((revision) => {
          const current = revision.id === selected.id;
          return (
            <li key={revision.id} className="shrink-0">
              <button
                type="button"
                onClick={() => onSelect(revision)}
                aria-current={current ? "true" : undefined}
                className={cn(
                  "flex w-full min-w-36 flex-col items-start gap-1.5 rounded-md border px-3 py-2.5 text-left transition-colors duration-150 ease-out",
                  current
                    ? "border-primary bg-status-sent-bg"
                    : "border-border bg-card hover:bg-accent",
                )}
              >
                <span className="flex w-full items-baseline justify-between gap-3">
                  <span
                    className={cn(
                      "text-base font-semibold",
                      current ? "text-primary" : "text-foreground",
                    )}
                  >
                    {revision.label}
                  </span>
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {formatShortDate(revision.uploaded_at)}
                  </span>
                </span>
                <StatusBadge status={revision.is_locked ? "locked" : revision.status} />
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/**
 * The design revisions of a project: the list (R3, R2, R1) and, for the selected one, the
 * large viewer with the approvals panel. Earlier revisions stay in the history (PR4).
 */
export function RevisionsTab({
  projectId,
  forClient = false,
  isApprover = false,
}: RevisionsTabProps) {
  const user = useCurrentUser();
  const revisions = useProjectRevisions(projectId);
  const [searchParams, setSearchParams] = useSearchParams();

  if (revisions.isPending) {
    return (
      <div aria-hidden="true" className="grid gap-6 lg:grid-cols-[13rem_1fr]">
        <Skeleton className="h-40 rounded-lg" />
        <Skeleton className="h-[28rem] rounded-lg" />
      </div>
    );
  }
  if (revisions.isError) {
    return (
      <Card>
        <ErrorState
          error={revisions.error}
          what="the design revisions"
          onRetry={() => void revisions.refetch()}
        />
      </Card>
    );
  }
  if (revisions.data.length === 0) {
    return (
      <Card>
        <EmptyState
          icon={PenTool}
          title="No design revision yet"
          description={
            forClient
              ? "Our designers upload the first design here once the quotation is accepted."
              : "The designer uploads the first revision (R1) once the quotation is accepted."
          }
        />
      </Card>
    );
  }

  const wanted = Number(searchParams.get("revision"));
  const selected =
    revisions.data.find((revision) => revision.revision_no === wanted) ?? revisions.data[0]!;
  const waitsForViewer =
    isApprover &&
    selected.status === "pending_approval" &&
    selected.approvals.some((line) => line.approver.id === user.id && line.state === "pending");

  return (
    <div className="grid gap-6 lg:grid-cols-[13rem_minmax(0,1fr)]">
      <RevisionList
        revisions={revisions.data}
        selected={selected}
        onSelect={(revision) =>
          setSearchParams(
            (current) => {
              const next = new URLSearchParams(current);
              next.set("revision", String(revision.revision_no));
              return next;
            },
            { replace: true },
          )
        }
      />
      <RevisionViewer revision={selected}>
        {waitsForViewer && (
          <p className="flex items-start gap-2 rounded-md border border-status-sent-border bg-status-sent-bg px-3 py-2 text-status-sent">
            <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <span>
              This design waits for your decision. The “Approve” and “Request changes” buttons
              arrive with Milestone 5 of the FabriSee build; until then, tell your project manager.
            </span>
          </p>
        )}
        <ApprovalPanel
          approvals={selected.approvals}
          approvedCount={selected.approved_count}
          approverCount={selected.approver_count}
          currentUserId={user.id}
        />
      </RevisionViewer>
    </div>
  );
}
