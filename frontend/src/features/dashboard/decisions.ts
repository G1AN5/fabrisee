import type { PendingDecision } from "@/lib/types";

/** Where a pending decision is shown in the staff workspace. */
export function decisionHref(decision: PendingDecision): string {
  const base = `/app/projects/${decision.project.id}`;
  if (decision.id === null) return base;
  return decision.kind === "quotation" ? `${base}/quotations` : `${base}/revisions`;
}

/** `Waiting for Mark Bautista` or `Waiting for 2 approvers`. */
export function pendingApproversText(decision: PendingDecision): string {
  const names = decision.pending_approvers.map((person) => person.full_name);
  if (names.length === 0) return "No designated approver";
  if (decision.kind === "quotation" && names.length > 1) {
    return `Waiting for one of ${names.length} approvers`;
  }
  if (names.length <= 2) return `Waiting for ${names.join(" and ")}`;
  return `Waiting for ${names.length} approvers`;
}
