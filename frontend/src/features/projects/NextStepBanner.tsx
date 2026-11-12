import { ArrowRight, CircleCheck, Hourglass, type LucideIcon, Wrench } from "lucide-react";
import type { ReactNode } from "react";

import type { NextStep } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Look {
  icon: LucideIcon;
  label: string;
  className: string;
}

function lookOf(step: NextStep, forClient: boolean): Look {
  if (step.action_needed) {
    return {
      icon: ArrowRight,
      label: forClient ? "Your action is needed" : "Next step: your action",
      className: "border-status-sent-border bg-status-sent-bg text-status-sent",
    };
  }
  if (step.waiting_on === "none") {
    return {
      icon: CircleCheck,
      label: "Status",
      className: "border-status-approved-border bg-status-approved-bg text-status-approved",
    };
  }
  if (step.waiting_on === "client") {
    return {
      icon: Hourglass,
      label: forClient ? "Waiting for a decision" : "Waiting for the client",
      className: "border-status-pending-border bg-status-pending-bg text-status-pending",
    };
  }
  return {
    icon: Wrench,
    label: forClient ? "What happens now" : "Next step",
    className: "border-status-neutral-border bg-status-neutral-bg text-status-neutral",
  };
}

interface NextStepBannerProps {
  step: NextStep;
  forClient?: boolean;
  /** A button for the person who has to act (for example "Review design R2"). */
  action?: ReactNode;
  /** Larger text, for the client portal. */
  large?: boolean;
}

/** What happens next on a project, in one sentence, with who it is waiting for. */
export function NextStepBanner({
  step,
  forClient = false,
  action,
  large = false,
}: NextStepBannerProps) {
  const look = lookOf(step, forClient);
  const Icon = look.icon;
  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-md border px-4 py-3 sm:flex-row sm:items-center sm:justify-between",
        look.className,
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <div>
          <p className="text-xs font-medium">{look.label}</p>
          <p className={cn("font-medium text-foreground", large ? "text-base" : "text-sm")}>
            {step.text}
          </p>
        </div>
      </div>
      {action && <div className="shrink-0 pl-7 sm:pl-0">{action}</div>}
    </div>
  );
}
