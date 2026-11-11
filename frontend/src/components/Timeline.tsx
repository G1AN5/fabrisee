import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface TimelineItem {
  id: string | number;
  icon: LucideIcon;
  /** Classes of the icon circle (for example the color of a stage). */
  iconClassName?: string;
  title: ReactNode;
  /** Who and when. */
  meta?: ReactNode;
  /** Remarks or a comment. */
  body?: ReactNode;
}

/** A vertical timeline, oldest or newest first as the caller orders it. */
export function Timeline({ items, className }: { items: TimelineItem[]; className?: string }) {
  return (
    <ol className={cn("flex flex-col", className)}>
      {items.map((item, index) => {
        const Icon = item.icon;
        const last = index === items.length - 1;
        return (
          <li key={item.id} className="grid grid-cols-[auto_1fr] gap-x-4">
            <div className="flex flex-col items-center">
              <span
                className={cn(
                  "flex size-9 shrink-0 items-center justify-center rounded-full border bg-card text-slate-600",
                  item.iconClassName,
                )}
              >
                <Icon className="size-4" aria-hidden="true" />
              </span>
              {!last && <span className="my-1 w-px flex-1 bg-border" aria-hidden="true" />}
            </div>
            <div className={cn("min-w-0 pt-1.5", last ? "pb-0" : "pb-6")}>
              <p className="font-medium text-foreground">{item.title}</p>
              {item.meta && <p className="mt-0.5 text-xs text-muted-foreground">{item.meta}</p>}
              {item.body && <div className="mt-2 text-foreground">{item.body}</div>}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
