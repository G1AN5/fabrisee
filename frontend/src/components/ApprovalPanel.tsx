import type { ReactNode } from "react";

import { RelativeTime } from "@/components/RelativeTime";
import { StatusBadge } from "@/components/StatusBadge";
import { Avatar } from "@/components/ui/avatar";
import { approvalSummary, onBehalfText } from "@/lib/approvals";
import type { ApprovalLine } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ApprovalPanelProps {
  approvals: ApprovalLine[];
  approvedCount: number;
  approverCount: number;
  /** Marks the line of the signed-in user with "(you)". */
  currentUserId?: number;
  /** Decision buttons for a designated approver (added with the approval flow). */
  footer?: ReactNode;
  className?: string;
}

/**
 * Who has to approve a design revision and what each of them decided: one line per
 * designated approver with the decision, the time, and the comment.
 */
export function ApprovalPanel({
  approvals,
  approvedCount,
  approverCount,
  currentUserId,
  footer,
  className,
}: ApprovalPanelProps) {
  return (
    <section className={cn("rounded-lg border bg-card", className)} aria-label="Approvals">
      <header className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 border-b px-4 py-3">
        <h3 className="text-sm font-semibold text-foreground">Approvals</h3>
        <p className="text-xs text-muted-foreground">
          {approvalSummary(approvedCount, approverCount)}
        </p>
      </header>
      {approvals.length === 0 ? (
        <p className="px-4 py-6 text-center text-muted-foreground">
          Nobody is designated to approve this project yet.
        </p>
      ) : (
        <ul className="divide-y">
          {approvals.map((line) => {
            const behalf = onBehalfText(line);
            return (
              <li key={line.approver.id} className="flex gap-3 px-4 py-3">
                <Avatar initials={line.approver.initials} className="mt-0.5" />
                <div className="flex min-w-0 flex-1 flex-col gap-1.5">
                  <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                    <p className="min-w-0 truncate font-medium text-foreground">
                      {line.approver.full_name}
                      {line.approver.id === currentUserId && (
                        <span className="font-normal text-muted-foreground"> (you)</span>
                      )}
                    </p>
                    <StatusBadge status={line.state} />
                  </div>
                  {line.decided_at && (
                    <p className="text-xs text-muted-foreground">
                      <RelativeTime value={line.decided_at} />
                      {behalf && <span> · {behalf}</span>}
                    </p>
                  )}
                  {line.comment && (
                    <blockquote className="rounded-md border-l-2 border-slate-300 bg-slate-50 px-3 py-2 text-foreground">
                      {line.comment}
                    </blockquote>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
      {footer && <footer className="border-t px-4 py-3">{footer}</footer>}
    </section>
  );
}
