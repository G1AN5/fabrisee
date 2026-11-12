import { ArrowLeft, ArrowRight, ChevronDown, FileText, Info } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { ProjectNumber } from "@/components/ProjectNumber";
import { StageChip } from "@/components/StageChip";
import { StageTracker } from "@/components/StageTracker";
import { StatusBadge } from "@/components/StatusBadge";
import { NotFoundPage } from "@/components/StatusPages";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DocumentsTab } from "@/features/documents/DocumentsTab";
import { ProgressTab } from "@/features/progress/ProgressTab";
import { useProject, useProjectQuotations } from "@/features/projects/api";
import { ApprovedDesignCard } from "@/features/projects/ApprovedDesignCard";
import { NextStepBanner } from "@/features/projects/NextStepBanner";
import { OverviewTab } from "@/features/projects/OverviewTab";
import { QuotationCard } from "@/features/quotations/QuotationCard";
import { RevisionsTab } from "@/features/revisions/RevisionsTab";
import { ApiError } from "@/lib/api";
import { PORTAL_PROJECT_TABS, type PortalProjectTab } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { ProjectDetail } from "@/lib/types";

/** The quotation tab of the client portal: the current version with its PDF, then earlier ones. */
function PortalQuotationTab({ project }: { project: ProjectDetail }) {
  const quotations = useProjectQuotations(project.id);

  if (quotations.isPending) {
    return <Skeleton aria-hidden="true" className="h-72 rounded-lg" />;
  }
  if (quotations.isError) {
    return (
      <Card>
        <ErrorState
          error={quotations.error}
          what="the quotation"
          onRetry={() => void quotations.refetch()}
        />
      </Card>
    );
  }
  const [current, ...earlier] = quotations.data;
  if (!current) {
    return (
      <Card>
        <EmptyState
          icon={FileText}
          title="No quotation yet"
          description="We are preparing your quotation. You will be notified when it is ready."
        />
      </Card>
    );
  }
  const waitsForViewer = current.status === "sent" && project.viewer.is_designated_approver;

  return (
    <div className="flex flex-col gap-4">
      {waitsForViewer && (
        <p className="flex items-start gap-2 rounded-md border border-status-sent-border bg-status-sent-bg px-3 py-2 text-status-sent">
          <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>
            This quotation waits for your decision. The “Accept” and “Return with comments” buttons
            arrive with Milestone 4 of the FabriSee build; until then, tell your project manager.
          </span>
        </p>
      )}
      <QuotationCard quotation={current} forClient preview />

      {earlier.length > 0 && (
        <details className="group rounded-lg border bg-card">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-lg px-5 py-4 font-medium text-foreground -outline-offset-2 [&::-webkit-details-marker]:hidden">
            Earlier versions ({earlier.length})
            <ChevronDown
              className="size-4 text-muted-foreground transition-transform duration-150 group-open:rotate-180"
              aria-hidden="true"
            />
          </summary>
          <div className="flex flex-col gap-4 border-t p-4">
            {earlier.map((quotation) => (
              <QuotationCard key={quotation.id} quotation={quotation} forClient />
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

/** A project in the client portal: a large stage tracker, the next step, and five tabs. */
export function PortalProjectPage() {
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
  const requested = params.tab as PortalProjectTab | undefined;
  const tab: PortalProjectTab =
    requested && PORTAL_PROJECT_TABS.some((item) => item.value === requested)
      ? requested
      : "summary";
  const base = `/portal/projects/${projectId}`;
  const item = data?.next_step.item;
  const actionTab = item?.kind === "quotation" ? "quotation" : "designs";

  return (
    <>
      <Link
        to="/portal"
        className="mb-4 inline-flex min-h-10 items-center gap-1.5 rounded-sm text-sm font-medium text-muted-foreground transition-colors duration-150 hover:text-foreground"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        My projects
      </Link>

      {!data ? (
        <div aria-hidden="true" className="flex flex-col gap-6">
          <Skeleton className="h-80 rounded-lg" />
          <Skeleton className="h-64 rounded-lg" />
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <Card className="flex flex-col gap-6 p-5 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <h1 className="text-2xl text-foreground">{data.title}</h1>
                <p className="mt-1 flex flex-wrap gap-x-2 text-muted-foreground">
                  <ProjectNumber value={data.project_number} />
                  <span>{data.project_type_label}</span>
                </p>
              </div>
              {data.status === "active" ? (
                <StageChip stage={data.stage} />
              ) : (
                <StatusBadge status={data.status} />
              )}
            </div>
            {/* On a phone, a decision that waits for this client comes before the tracker,
                so the button is on the first screen. */}
            <div className={cn(data.next_step.action_needed && "max-sm:order-2")}>
              <StageTracker stage={data.stage} stageDates={data.stage_dates} status={data.status} />
            </div>
            <div className={cn(data.next_step.action_needed && "max-sm:order-1")}>
              <NextStepBanner
                step={data.next_step}
                forClient
                large
                action={
                  data.next_step.action_needed && item && tab !== actionTab ? (
                    <Button asChild>
                      <Link to={`${base}/${actionTab}`}>
                        Review now
                        <ArrowRight aria-hidden="true" />
                      </Link>
                    </Button>
                  ) : undefined
                }
              />
            </div>
          </Card>

          {data.approved_revision && (
            <ApprovedDesignCard
              revision={data.approved_revision}
              viewHref={`${base}/designs?revision=${data.approved_revision.revision_no}`}
              reopened={data.design_reopened}
            />
          )}

          <Tabs
            value={tab}
            onValueChange={(value) => navigate(value === "summary" ? base : `${base}/${value}`)}
          >
            <TabsList aria-label="Project sections">
              {PORTAL_PROJECT_TABS.map((tabItem) => (
                <TabsTrigger key={tabItem.value} value={tabItem.value}>
                  {tabItem.label}
                </TabsTrigger>
              ))}
            </TabsList>
            <TabsContent value="summary">
              <OverviewTab project={data} forClient />
            </TabsContent>
            <TabsContent value="quotation">
              <PortalQuotationTab project={data} />
            </TabsContent>
            <TabsContent value="designs">
              <RevisionsTab
                projectId={projectId}
                forClient
                isApprover={data.viewer.is_designated_approver}
              />
            </TabsContent>
            <TabsContent value="progress">
              <ProgressTab projectId={projectId} forClient />
            </TabsContent>
            <TabsContent value="documents">
              <DocumentsTab projectId={projectId} forClient />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </>
  );
}
