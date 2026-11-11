import { CircleAlert, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { errorMessage } from "@/lib/errors";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
  /** What could not be loaded, for example "the projects". */
  what?: string;
  compact?: boolean;
  className?: string;
}

/** Shown when loading failed: a plain message and a way to try again. */
export function ErrorState({ error, onRetry, what, compact = false, className }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center text-center",
        compact ? "gap-2 px-4 py-8" : "gap-3 px-4 py-14",
        className,
      )}
    >
      <span className="flex size-11 items-center justify-center rounded-full bg-status-changes-bg text-status-changes">
        <CircleAlert className="size-5" aria-hidden="true" />
      </span>
      <p className="font-medium text-foreground">
        {what ? `We could not load ${what}` : "We could not load this"}
      </p>
      <p className="max-w-md text-muted-foreground">{errorMessage(error)}</p>
      {onRetry && (
        <Button variant="outline" className="mt-2" onClick={onRetry}>
          <RefreshCw aria-hidden="true" />
          Try again
        </Button>
      )}
    </div>
  );
}
