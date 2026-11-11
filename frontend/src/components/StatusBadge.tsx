import {
  Ban,
  CircleAlert,
  CircleCheck,
  CirclePause,
  CirclePlay,
  Clock,
  History,
  Lock,
  type LucideIcon,
  Minus,
  PencilLine,
  Send,
  TriangleAlert,
  Undo2,
} from "lucide-react";

import { cn } from "@/lib/utils";

type Tone = "pending" | "approved" | "changes" | "sent" | "neutral";

const TONES: Record<Tone, string> = {
  pending: "bg-status-pending-bg text-status-pending border-status-pending-border",
  approved: "bg-status-approved-bg text-status-approved border-status-approved-border",
  changes: "bg-status-changes-bg text-status-changes border-status-changes-border",
  sent: "bg-status-sent-bg text-status-sent border-status-sent-border",
  neutral: "bg-status-neutral-bg text-status-neutral border-status-neutral-border",
};

const STATUSES = {
  // Quotations
  draft: { label: "Draft", tone: "neutral", icon: PencilLine },
  sent: { label: "Sent", tone: "sent", icon: Send },
  accepted: { label: "Accepted", tone: "approved", icon: CircleCheck },
  returned: { label: "Returned", tone: "changes", icon: Undo2 },
  superseded: { label: "Superseded", tone: "neutral", icon: History },
  // Design revisions and approvals
  pending_approval: { label: "Pending approval", tone: "pending", icon: Clock },
  changes_requested: { label: "Changes requested", tone: "changes", icon: CircleAlert },
  approved: { label: "Approved", tone: "approved", icon: CircleCheck },
  locked: { label: "Approved and locked", tone: "approved", icon: Lock },
  pending: { label: "Waiting for decision", tone: "pending", icon: Clock },
  no_decision: { label: "No decision", tone: "neutral", icon: Minus },
  // Projects
  active: { label: "Active", tone: "sent", icon: CirclePlay },
  on_hold: { label: "On hold", tone: "pending", icon: CirclePause },
  cancelled: { label: "Cancelled", tone: "neutral", icon: Ban },
  completed: { label: "Completed", tone: "approved", icon: CircleCheck },
  overdue: { label: "Overdue", tone: "changes", icon: TriangleAlert },
} as const satisfies Record<string, { label: string; tone: Tone; icon: LucideIcon }>;

export type StatusKey = keyof typeof STATUSES;

interface StatusBadgeProps {
  status: StatusKey;
  /** Replace the default label (for example "Overdue by 2 days"). */
  label?: string;
  className?: string;
}

/** A status as text with a color and an icon: never color alone. */
export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const info = STATUSES[status];
  const Icon = info.icon;
  return (
    <span
      className={cn(
        "inline-flex w-fit shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap",
        TONES[info.tone],
        className,
      )}
    >
      <Icon className="size-3.5 shrink-0" aria-hidden="true" />
      {label ?? info.label}
    </span>
  );
}
