import { FileText, PenTool } from "lucide-react";
import { Link } from "react-router";

import { ProjectNumber } from "@/components/ProjectNumber";
import { RelativeTime } from "@/components/RelativeTime";
import { StatusBadge } from "@/components/StatusBadge";
import { decisionHref, pendingApproversText } from "@/features/dashboard/decisions";
import { formatWaiting } from "@/lib/format";
import type { PendingDecision } from "@/lib/types";
import { cn } from "@/lib/utils";

interface PendingDecisionListProps {
  decisions: PendingDecision[];
  /** Show the time of the last reminder (the Approvals page). */
  showReminders?: boolean;
  className?: string;
}

/** Quotations and design revisions that wait for a client decision, longest wait first. */
export function PendingDecisionList({
  decisions,
  showReminders = false,
  className,
}: PendingDecisionListProps) {
  return (
    <ul className={cn("flex flex-col divide-y", className)}>
      {decisions.map((decision) => {
        const Icon = decision.kind === "quotation" ? FileText : PenTool;
        return (
          <li key={`${decision.kind}-${decision.project.id}-${decision.label}`}>
            <Link
              to={decisionHref(decision)}
              className="flex flex-col gap-2 px-5 py-3 transition-colors duration-150 -outline-offset-2 hover:bg-slate-50 sm:flex-row sm:items-center sm:gap-4 sm:px-6"
            >
              <span className="flex min-w-0 flex-1 items-start gap-3">
                <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-muted text-slate-600">
                  <Icon className="size-4" aria-hidden="true" />
                </span>
                <span className="min-w-0">
                  <span className="block truncate font-medium text-foreground">
                    {decision.label}
                    <span className="font-normal text-muted-foreground">
                      {" "}
                      · {decision.project.title}
                    </span>
                  </span>
                  <span className="flex flex-wrap gap-x-2 text-xs text-muted-foreground">
                    <ProjectNumber value={decision.project.project_number} />
                    <span>{decision.project.client_name}</span>
                    <span>
                      {pendingApproversText(decision)}
                      {decision.approver_count > 1 && decision.kind === "revision"
                        ? ` (${decision.decided_count} of ${decision.approver_count} approved)`
                        : ""}
                    </span>
                  </span>
                  {showReminders && (
                    <span className="mt-0.5 block text-xs text-muted-foreground">
                      {decision.last_reminded_at ? (
                        <>
                          Last reminder <RelativeTime value={decision.last_reminded_at} />
                        </>
                      ) : (
                        "No reminder sent yet"
                      )}
                    </span>
                  )}
                </span>
              </span>
              <span className="flex shrink-0 items-center gap-2 pl-11 sm:pl-0">
                <span
                  className={cn(
                    "text-sm tabular-nums",
                    decision.is_overdue ? "font-medium text-destructive" : "text-muted-foreground",
                  )}
                  title={`Waiting since the ${decision.kind} was ${decision.kind === "quotation" ? "sent" : "uploaded"}`}
                >
                  {formatWaiting(decision.waiting_hours)}
                </span>
                {decision.is_overdue ? (
                  <StatusBadge status="overdue" />
                ) : (
                  <StatusBadge status="pending" label="Waiting" />
                )}
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
