import { BellRing } from "lucide-react";
import { Link } from "react-router";

import { ProjectNumber } from "@/components/ProjectNumber";
import { RelativeTime } from "@/components/RelativeTime";
import { Avatar } from "@/components/ui/avatar";
import type { ActivityEntry } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ActivityFeedProps {
  entries: ActivityEntry[];
  /** Builds the link to a project (when entries of several projects are shown). */
  projectHref?: (projectId: number) => string;
  className?: string;
}

/** Who did what and when, newest first. */
export function ActivityFeed({ entries, projectHref, className }: ActivityFeedProps) {
  return (
    <ul className={cn("flex flex-col divide-y", className)}>
      {entries.map((entry) => (
        <li key={entry.id} className="flex gap-3 py-3 first:pt-0 last:pb-0">
          {entry.actor ? (
            <Avatar initials={entry.actor.initials} className="mt-0.5" />
          ) : (
            <span
              aria-hidden="true"
              className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-status-pending-bg text-status-pending"
            >
              <BellRing className="size-4" />
            </span>
          )}
          <div className="min-w-0 flex-1">
            <p className="text-foreground">
              {entry.actor_name && <span className="font-medium">{entry.actor_name} </span>}
              {entry.text}
            </p>
            <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
              {entry.project && projectHref && (
                <Link
                  to={projectHref(entry.project.id)}
                  className="max-w-full truncate text-link underline-offset-2 hover:underline"
                  title={entry.project.title}
                >
                  <ProjectNumber value={entry.project.project_number} />
                </Link>
              )}
              <RelativeTime value={entry.created_at} />
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}
