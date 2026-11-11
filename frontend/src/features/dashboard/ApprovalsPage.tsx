import { CircleCheck } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePendingApprovals } from "@/features/dashboard/api";
import { PendingDecisionList } from "@/features/dashboard/PendingDecisionList";

/** Every quotation and design revision that waits for a client decision (read-only). */
export function ApprovalsPage() {
  const approvals = usePendingApprovals();
  const data = approvals.data;

  return (
    <>
      <PageHeader
        title="Approvals"
        description={
          data
            ? data.count === 0
              ? "No decision is pending."
              : `${data.count} pending ${data.count === 1 ? "decision" : "decisions"}, ${data.overdue_count} overdue. Longest wait first.`
            : "Quotations and design revisions waiting for a client decision."
        }
      />
      <Card>
        {approvals.isPending && (
          <div aria-hidden="true" className="flex flex-col gap-3 p-5">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        )}
        {approvals.isError && (
          <ErrorState
            error={approvals.error}
            what="the pending decisions"
            onRetry={() => void approvals.refetch()}
          />
        )}
        {data && data.count === 0 && (
          <EmptyState
            icon={CircleCheck}
            title="No decision is pending"
            description="Quotations and design revisions appear here while they wait for a client decision."
          />
        )}
        {data && data.count > 0 && (
          <PendingDecisionList decisions={data.results} showReminders className="py-1" />
        )}
      </Card>
      <p className="mt-4 text-xs text-muted-foreground">
        Reminders to approvers and “Remind now” arrive with Milestone 7 of the FabriSee build.
      </p>
    </>
  );
}
