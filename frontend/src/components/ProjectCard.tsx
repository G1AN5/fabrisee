import { ArrowRight, CalendarDays } from "lucide-react";
import { Link } from "react-router";

import { ProjectNumber } from "@/components/ProjectNumber";
import { RelativeTime } from "@/components/RelativeTime";
import { StageChip } from "@/components/StageChip";
import { StageSteps } from "@/components/StageTracker";
import { StatusBadge } from "@/components/StatusBadge";
import { describeDue, formatDate, formatShortDate } from "@/lib/format";
import type { ProjectCardData } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ProjectCardProps {
  project: ProjectCardData;
  to: string;
  /**
   * `compact`: number, title, client, target date, next step (dashboard columns).
   * `full`: adds the stage and the last update (the client's project list).
   */
  variant?: "compact" | "full";
  /** Hide the client name (in the client portal every project is the client's own). */
  hideClient?: boolean;
  /** Name the project manager (the staff list on narrow screens, where there is no table). */
  showManager?: boolean;
}

export function ProjectCard({
  project,
  to,
  variant = "compact",
  hideClient = false,
  showManager = false,
}: ProjectCardProps) {
  const open = project.status === "active" || project.status === "on_hold";

  if (variant === "compact") {
    return (
      <Link
        to={to}
        className="block rounded-md border bg-card p-3 shadow-xs transition-[border-color,box-shadow] duration-150 ease-out hover:border-slate-300 hover:shadow-sm"
      >
        <span className="flex items-center justify-between gap-2 text-xs">
          <ProjectNumber value={project.project_number} className="text-muted-foreground" />
          <span
            className={cn(
              "shrink-0 tabular-nums",
              project.is_overdue ? "font-medium text-destructive" : "text-muted-foreground",
            )}
            title={open ? describeDue(project.days_until_target) : undefined}
          >
            {project.is_overdue && <span className="sr-only">Overdue: </span>}
            {formatShortDate(project.target_date)}
          </span>
        </span>
        <span className="mt-1 line-clamp-2 font-medium text-foreground" title={project.title}>
          {project.title}
        </span>
        {!hideClient && (
          <span className="block truncate text-xs text-muted-foreground">
            {project.client.company_name}
          </span>
        )}
        <span className="mt-2 line-clamp-2 block text-xs text-slate-700">
          {project.next_step.text}
        </span>
      </Link>
    );
  }

  const action = project.next_step.action_needed;
  return (
    <Link
      to={to}
      className={cn(
        "group flex flex-col gap-4 rounded-lg border bg-card p-5 shadow-xs transition-[border-color,box-shadow] duration-150 ease-out hover:border-slate-300 hover:shadow-sm",
        action && "border-status-pending-border",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-base font-semibold text-foreground" title={project.title}>
            {project.title}
          </p>
          <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
            <ProjectNumber value={project.project_number} />
            {!hideClient && <span>{project.client.company_name}</span>}
            <span>{project.project_type_label}</span>
          </p>
          {showManager && (
            <p className="mt-0.5 text-xs text-muted-foreground">
              Manager: {project.manager?.full_name ?? "not assigned"}
            </p>
          )}
        </div>
        {project.status === "active" ? (
          <StageChip stage={project.stage} short className="mt-0.5" />
        ) : (
          <StatusBadge status={project.status} className="mt-0.5" />
        )}
      </div>

      <div className="flex flex-col gap-2">
        <StageSteps stage={project.stage} status={project.status} />
        <p className={cn("text-foreground", action && "font-medium")}>{project.next_step.text}</p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <CalendarDays className="size-3.5" aria-hidden="true" />
          <span>
            Target date{" "}
            <span
              className={cn(
                "tabular-nums",
                project.is_overdue ? "font-medium text-destructive" : "text-foreground",
              )}
            >
              {formatDate(project.target_date)}
            </span>
          </span>
        </span>
        <span className="flex items-center gap-1.5">
          Updated <RelativeTime value={project.last_activity_at} />
          <ArrowRight
            className="size-3.5 text-slate-400 transition-transform duration-150 group-hover:translate-x-0.5"
            aria-hidden="true"
          />
        </span>
      </div>
    </Link>
  );
}
