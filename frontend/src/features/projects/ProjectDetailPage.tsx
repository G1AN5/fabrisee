import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { ErrorState } from "@/components/ErrorState";
import { ProjectNumber } from "@/components/ProjectNumber";
import { StageChip } from "@/components/StageChip";
import { StageTracker } from "@/components/StageTracker";
import { StatusBadge } from "@/components/StatusBadge";
import { NotFoundPage } from "@/components/StatusPages";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DocumentsTab } from "@/features/documents/DocumentsTab";
import { ProgressTab } from "@/features/progress/ProgressTab";
import { ActivityTab } from "@/features/projects/ActivityTab";
import { useProject } from "@/features/projects/api";
import { ApprovedDesignCard } from "@/features/projects/ApprovedDesignCard";
import { NextStepBanner } from "@/features/projects/NextStepBanner";
import { OverviewTab } from "@/features/projects/OverviewTab";
import { QuotationsTab } from "@/features/quotations/QuotationsTab";
import { RevisionsTab } from "@/features/revisions/RevisionsTab";
import { ApiError } from "@/lib/api";
import { STAFF_PROJECT_TABS, type StaffProjectTab } from "@/lib/constants";
import { describeDue, formatDate } from "@/lib/format";
import type { ProjectDetail } from "@/lib/types";
import { cn } from "@/lib/utils";

function HeaderField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-0.5 truncate text-foreground">{children}</dd>
    </div>
  );
}

function ProjectHeader({ project }: { project: ProjectDetail }) {
  const open = project.status === "active" || project.status === "on_hold";
  return (
    <Card className="flex flex-col gap-6 p-5 sm:p-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <ProjectNumber value={project.project_number} className="text-muted-foreground" />
            <StageChip stage={project.stage} />
            {project.status !== "active" && <StatusBadge status={project.status} />}
            {project.is_overdue && (
              <StatusBadge status="overdue" label={describeDue(project.days_until_target)} />
            )}
          </div>
          <h1 className="mt-2 text-2xl text-foreground">{project.title}</h1>
          <p className="mt-1 text-muted-foreground">
            {project.client.company_name} · {project.project_type_label}
          </p>
        </div>
        <dl className="grid shrink-0 grid-cols-2 gap-x-8 gap-y-3 sm:grid-cols-3 lg:max-w-md">
          <HeaderField label="Target date">
            <span
              className={cn("tabular-nums", project.is_overdue && "font-medium text-destructive")}
            >
              {formatDate(project.target_date)}
            </span>
            {open && !project.is_overdue && (
              <span className="block text-xs text-muted-foreground">
                {describeDue(project.days_until_target)}
              </span>
            )}
          </HeaderField>
          <HeaderField label="Manager">
            {project.manager?.full_name ?? <span className="text-muted-foreground">None</span>}
          </HeaderField>
          <HeaderField label="Designer">
            {project.designer?.full_name ?? (
              <span className="text-muted-foreground">Not assigned</span>
            )}
          </HeaderField>
        </dl>
      </div>
      <StageTracker
        stage={project.stage}
        stageDates={project.stage_dates}
        status={project.status}
      />
      <NextStepBanner step={project.next_step} />
    </Card>
  );
}

function HeaderSkeleton() {
  return (
    <div aria-hidden="true" className="flex flex-col gap-6">
      <Skeleton className="h-72 rounded-lg" />
      <Skeleton className="h-11 w-full max-w-xl" />
      <Skeleton className="h-64 rounded-lg" />
    </div>
  );
}

/** A project in the staff workspace: header, approved design, and six tabs (read-only). */
export function ProjectDetailPage() {
  const params = useParams();
  const navigate = useNavigate();
  const projectId = Number(params.projectId);
  const project = useProject(projectId);

  if (!Number.isInteger(projectId) || projectId <= 0) return <NotFoundPage what="project" />;
  if (project.isError) {
    if (project.error instanceof ApiError && project.error.status === 404) {
      return <NotFoundPage what="project" />;
    }
    return (
      <Card>
        <ErrorState
          error={project.error}
          what="this project"
          onRetry={() => void project.refetch()}
        />
      </Card>
    );
  }

  const data = project.data;
  const tabs = STAFF_PROJECT_TABS.filter(
    (tab) => tab.value !== "quotations" || (data?.viewer.can_view_quotations ?? true),
  );
  const requested = params.tab as StaffProjectTab | undefined;
  const tab: StaffProjectTab =
    requested && tabs.some((item) => item.value === requested) ? requested : "overview";
  const base = `/app/projects/${projectId}`;

  return (
    <>
      <Link
        to="/app/projects"
        className="mb-4 inline-flex items-center gap-1.5 rounded-sm text-sm font-medium text-muted-foreground transition-colors duration-150 hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        Projects
      </Link>

      {!data ? (
        <HeaderSkeleton />
      ) : (
        <div className="flex flex-col gap-6">
          <ProjectHeader project={data} />
          {data.approved_revision && (
            <ApprovedDesignCard
              revision={data.approved_revision}
              viewHref={`${base}/revisions?revision=${data.approved_revision.revision_no}`}
              reopened={data.design_reopened}
            />
          )}
          <Tabs
            value={tab}
            onValueChange={(value) => navigate(value === "overview" ? base : `${base}/${value}`)}
          >
            <TabsList aria-label="Project sections">
              {tabs.map((item) => (
                <TabsTrigger key={item.value} value={item.value}>
                  {item.label}
                  {item.value === "quotations" && data.counts.quotations > 0 && (
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {data.counts.quotations}
                    </span>
                  )}
                  {item.value === "revisions" && data.counts.revisions > 0 && (
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {data.counts.revisions}
                    </span>
                  )}
                  {item.value === "documents" && data.counts.documents > 0 && (
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {data.counts.documents}
                    </span>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
            <TabsContent value="overview">
              <OverviewTab project={data} />
            </TabsContent>
            <TabsContent value="quotations">
              <QuotationsTab projectId={projectId} />
            </TabsContent>
            <TabsContent value="revisions">
              <RevisionsTab projectId={projectId} />
            </TabsContent>
            <TabsContent value="progress">
              <ProgressTab projectId={projectId} />
            </TabsContent>
            <TabsContent value="documents">
              <DocumentsTab projectId={projectId} showVisibility />
            </TabsContent>
            <TabsContent value="activity">
              <ActivityTab projectId={projectId} />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </>
  );
}
