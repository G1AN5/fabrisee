import type * as React from "react";

import { cn } from "@/lib/utils";

/** Initials in a circle. FabriSee keeps no profile photos (data minimization). */
function Avatar({
  initials,
  className,
  ...props
}: React.ComponentProps<"span"> & { initials: string }) {
  return (
    <span
      data-slot="avatar"
      aria-hidden="true"
      className={cn(
        "inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-semibold text-slate-700 select-none",
        className,
      )}
      {...props}
    >
      {initials}
    </span>
  );
}

export { Avatar };
