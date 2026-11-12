import type * as React from "react";

import { cn } from "@/lib/utils";

/** A placeholder block shown while data loads; match the size of the real content. */
function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      aria-hidden="true"
      className={cn("animate-pulse rounded-md bg-slate-200/80", className)}
      {...props}
    />
  );
}

export { Skeleton };
