import {
  CalendarClock,
  CircleCheck,
  FolderKanban,
  Hourglass,
  Inbox,
  TriangleAlert,
} from "lucide-react";
import { Link } from "react-router";

import { ActivityFeed } from "@/components/ActivityFeed";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader } from "@/components/PageHeader";
import { ProjectCard } from "@/components/ProjectCard";
import { ProjectNumber } from "@/components/ProjectNumber";
import { StageChip } from "@/components/StageChip";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/features/dashboard/api";
import { PendingDecisionList } from "@/features/dashboard/PendingDecisionList";
import { useAuth, useCurrentUser } from "@/lib/auth";
import { describeDue, formatDate, formatLongDate, greeting } from "@/lib/format";
import type { Dashboard, ProjectCardData } from "@/lib/types";

function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

function DashboardSkeleton() {
  return (
    <div aria-hidden="true" className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <Skeleton key={index} className="h-32 rounded-lg" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Skeleton className="h-80 rounded-lg lg:col-span-2" />
        <Skeleton className="h-80 rounded-lg" />
      </div>
      <Skeleton className="h-72 rounded-lg" />
    </div>
  );
}

/** A project past its target date, or due soon, as one row. */
function ProjectRow({ project }: { project: ProjectCardData }) {
  return (
    <li>
      <Link
        to={`/app/projects/${project.id}`}
        className="flex flex-col gap-1 px-5 py-3 transition-colors duration-150 -outline-offset-2 hover:bg-slate-50 sm:flex-row sm:items-center sm:gap-4 sm:px-6"
      >
        <span className="min-w-0 flex-1">
          <span className="block truncate font-medium text-foreground">{project.title}</span>
          <span className="flex flex-wrap gap-x-2 text-xs text-muted-foreground">
            <ProjectNumber value={project.project_number} />
            <span>{project.client.company_name}</span>
          </span>
        </span>
        <span className="flex shrink-0 flex-wrap items-center gap-2">
          <StageChip stage={project.stage} short />
          <span
            className={
              project.is_overdue
                ? "text-sm font-medium text-destructive tabular-nums"
                : "text-sm text-muted-foreground tabular-nums"
            }
            title={`Target date ${formatDate(project.target_date)}`}
          >
            {describeDue(project.days_until_target)}
          </span>
        </span>
      </Link>
    </li>
  );
}

function NeedsAttention({ data }: { data: Dashboard }) {
  const nothing = data.pending_decisions.length === 0 && data.overdue_projects.length === 0;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Needs attention</CardTitle>
        <CardDescription>
          Decisions waiting for clients and projects past their target date. A decision is overdue
          after {data.reminder_hours} hours.
        </CardDescription>
      </CardHeader>
      {nothing ? (
        <EmptyState
          compact
          icon={CircleCheck}
          title="Nothing needs attention right now"
          description="No client decision is pending and no project is past its target date."
        />
      ) : (
        <div className="flex flex-col pb-2">
          {data.pending_decisions.length > 0 && (
            <section aria-labelledby="waiting-heading">
              <h3
                id="waiting-heading"
                className="border-y bg-slate-50 px-5 py-2 text-xs font-medium text-muted-foreground sm:px-6"
              >
                Waiting for a client decision
              </h3>
              <PendingDecisionList decisions={data.pending_decisions} />
            </section>
          )}
          {data.overdue_projects.length > 0 && (
            <section aria-labelledby="late-heading">
              <h3
                id="late-heading"
                className="border-y bg-slate-50 px-5 py-2 text-xs font-medium text-muted-foreground sm:px-6"
              >
                Past the target date
              </h3>
              <ul className="flex flex-col divide-y">
                {data.overdue_projects.map((project) => (
                  <ProjectRow key={project.id} project={project} />
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </Card>
  );
}

function DueSoon({ data }: { data: Dashboard }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Due in the next 7 days</CardTitle>
      </CardHeader>
      {data.due_soon.length === 0 ? (
        <p className="px-5 pb-6 text-muted-foreground sm:px-6">
          No project is due in the next 7 days.
        </p>
      ) : (
        <ul className="flex flex-col divide-y border-t pb-2">
          {data.due_soon.map((project) => (
            <ProjectRow key={project.id} project={project} />
          ))}
        </ul>
      )}
    </Card>
  );
}

function RecentActivity({ data }: { data: Dashboard }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent activity</CardTitle>
      </CardHeader>
      <CardContent>
        {data.recent_activity.length === 0 ? (
          <p className="py-6 text-center text-muted-foreground">No activity yet.</p>
        ) : (
          <ActivityFeed
            entries={data.recent_activity}
            projectHref={(id) => `/app/projects/${id}`}
          />
        )}
      </CardContent>
    </Card>
  );
}

function Focus({ focus }: { focus: NonNullable<Dashboard["focus"]> }) {
  return (
    <section aria-labelledby="focus-heading" className="mb-6">
      <h2 id="focus-heading" className="mb-3 text-base font-semibold">
        {focus.title}
        <span className="ml-2 font-normal text-muted-foreground tabular-nums">
          {focus.projects.length}
        </span>
      </h2>
      {focus.projects.length === 0 ? (
        <Card>
          <EmptyState compact icon={CircleCheck} title={focus.empty_text} />
        </Card>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {focus.projects.map((project) => (
            <li key={project.id}>
              <ProjectCard project={project} to={`/app/projects/${project.id}`} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function StageColumns({ data }: { data: Dashboard }) {
  return (
    <section aria-labelledby="stages-heading">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="stages-heading" className="text-base font-semibold">
          Projects by stage
        </h2>
        <p className="text-xs text-muted-foreground">
          Stages change through quotations, approvals, and progress updates, not here.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {data.by_stage.map((column) => (
          <section
            key={column.stage}
            aria-label={`${column.stage_label}: ${plural(column.count, "project", "projects")}`}
            className="flex min-w-0 flex-col rounded-lg border bg-slate-100/70 p-3"
          >
            <header className="mb-3 flex items-center justify-between gap-2">
              <StageChip stage={column.stage} />
              <span className="text-sm font-semibold text-foreground tabular-nums">
                {column.count}
              </span>
            </header>
            {column.projects.length === 0 ? (
              <p className="flex flex-1 items-center justify-center rounded-md border border-dashed border-slate-300 px-3 py-6 text-center text-xs text-muted-foreground">
                No projects in this stage
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {column.projects.map((project) => (
                  <li key={project.id}>
                    <ProjectCard project={project} to={`/app/projects/${project.id}`} />
                  </li>
                ))}
              </ul>
            )}
            {column.count > column.projects.length && (
              <Link
                to={
                  column.stage === "turnover"
                    ? "/app/projects?status=completed"
                    : `/app/projects?stage=${column.stage}`
                }
                className="mt-3 rounded-sm text-center text-xs font-medium text-link underline-offset-2 hover:underline"
              >
                View all {column.count}
              </Link>
            )}
          </section>
        ))}
      </div>
    </section>
  );
}

/** The management dashboard of the staff workspace (read-only). */
export function DashboardPage() {
  const user = useCurrentUser();
  const { can } = useAuth();
  const dashboard = useDashboard();
  const firstName = user.full_name.split(" ")[0];
  const data = dashboard.data;
  const showActivity = can("view_activity_log");

  return (
    <>
      <PageHeader title={`${greeting()}, ${firstName}`} description={formatLongDate(new Date())} />
      {dashboard.isPending && <DashboardSkeleton />}
      {dashboard.isError && (
        <Card>
          <ErrorState
            error={dashboard.error}
            what="the dashboard"
            onRetry={() => void dashboard.refetch()}
          />
        </Card>
      )}
      {data && (
        <div className="flex flex-col gap-6">
          {data.focus && <Focus focus={data.focus} />}
          <section aria-label="Key numbers" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <KpiCard
              label="Active projects"
              value={data.kpis.active_projects}
              hint="In progress now"
              icon={FolderKanban}
              to="/app/projects?status=active"
            />
            <KpiCard
              label="Waiting for client decisions"
              value={data.kpis.waiting_for_client}
              hint={
                data.kpis.overdue_decisions > 0
                  ? `${data.kpis.overdue_decisions} longer than ${data.reminder_hours} hours`
                  : "Quotations and design revisions"
              }
              icon={Hourglass}
              to={can("view_approvals") ? "/app/approvals" : "/app/projects?waiting_on=client"}
            />
            <KpiCard
              label="Overdue items"
              value={data.kpis.overdue_items}
              hint={`${plural(data.kpis.overdue_decisions, "decision", "decisions")} · ${plural(
                data.kpis.overdue_projects,
                "project",
                "projects",
              )}`}
              icon={TriangleAlert}
              to="/app/projects?overdue=1"
              alert
            />
            <KpiCard
              label="Due in the next 7 days"
              value={data.kpis.due_next_7_days}
              hint="By target date"
              icon={CalendarClock}
              to="/app/projects?due_within=7"
            />
          </section>
          {/* The activity feed is for administrators and project managers; other roles
              see what is due soon next to what needs attention. */}
          <div className="grid items-start gap-6 lg:grid-cols-3">
            <div className="flex flex-col gap-6 lg:col-span-2">
              <NeedsAttention data={data} />
              {showActivity && <DueSoon data={data} />}
            </div>
            {showActivity ? <RecentActivity data={data} /> : <DueSoon data={data} />}
          </div>
          {data.kpis.active_projects === 0 && data.stage_counts.turnover === 0 ? (
            <Card>
              <EmptyState
                icon={Inbox}
                title="There are no projects yet"
                description="A project starts when a client submits a request, or when staff record one on the client's behalf."
              />
            </Card>
          ) : (
            <StageColumns data={data} />
          )}
        </div>
      )}
    </>
  );
}
