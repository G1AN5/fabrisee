import type { ApprovalLine } from "@/lib/types";

/** `Recorded by A. Villanueva on behalf of N. Ramos (phone)`, or null for a portal decision. */
export function onBehalfText(line: ApprovalLine): string | null {
  if (!line.decided_on_behalf) return null;
  const recorder = line.recorded_by?.short_name ?? "staff";
  const channel = line.decision_channel_label
    ? ` (${line.decision_channel_label.toLowerCase()})`
    : "";
  return `Recorded by ${recorder} on behalf of ${line.approver.short_name}${channel}`;
}

export function approvalSummary(approvedCount: number, approverCount: number): string {
  if (approverCount === 0) return "No designated approvers yet";
  if (approvedCount === approverCount) {
    return approverCount === 1
      ? "Approved by the designated approver"
      : "Approved by all designated approvers";
  }
  return `${approvedCount} of ${approverCount} approved`;
}
