import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: ReactNode;
  /** The one thing the person can do next (a button or a link). */
  action?: ReactNode;
  /** Less padding, for an empty section inside a card. */
  compact?: boolean;
  className?: string;
}

/** Shown where there is nothing yet: an icon, one sentence, and a primary action. */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  compact = false,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center text-center",
        compact ? "gap-2 px-4 py-8" : "gap-3 px-4 py-14",
        className,
      )}
    >
      <span className="flex size-11 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <p className="font-medium text-foreground">{title}</p>
      {description && <p className="max-w-md text-muted-foreground">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
