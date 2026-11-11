import { ArrowRight, CirclePlus, FileText, FolderOpen, PenTool } from "lucide-react";
import { Link } from "react-router";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { ProjectCard } from "@/components/ProjectCard";
import { ProjectNumber } from "@/components/ProjectNumber";
import { RelativeTime } from "@/components/RelativeTime";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjects } from "@/features/projects/api";
import { useCurrentUser } from "@/lib/auth";
import type { ProjectCardData } from "@/lib/types";

/** Where the client decides: the quotation tab or the designs tab of the project. */
function actionHref(project: ProjectCardData): string {
  const tab = project.next_step.item?.kind === "quotation" ? "quotation" : "designs";
  return `/portal/projects/${project.id}/${tab}`;
}

function ActionCard({ project }: { project: ProjectCardData }) {
  const item = project.next_step.item;
  const Icon = item?.kind === "quotation" ? FileText : PenTool;
  return (
    <li className="flex flex-col gap-4 rounded-lg border border-status-pending-border bg-card p-5 shadow-xs sm:flex-row sm:items-center">
      <span className="flex min-w-0 flex-1 items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-status-pending-bg text-status-pending">
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <span className="min-w-0">
          <span className="block text-base font-semibold text-foreground">
            {project.next_step.text}
          </span>
          <span className="block truncate text-muted-foreground">{project.title}</span>
          <span className="mt-0.5 flex flex-wrap gap-x-2 text-xs text-muted-foreground">
            <ProjectNumber value={project.project_number} />
            {project.next_step.since && (
              <span>
                Waiting since <RelativeTime value={project.next_step.since} />
              </span>
            )}
          </span>
        </span>
      </span>
      <Button asChild size="lg" className="w-full sm:w-auto">
        <Link to={actionHref(project)}>
          {item ? `Review ${item.label.toLowerCase().replace("design r", "design R")}` : "Review"}
          <ArrowRight aria-hidden="true" />
        </Link>
      </Button>
    </li>
  );
}

/** The start page of the client portal: what needs a decision, then all projects. */
export function PortalHomePage() {
  const user = useCurrentUser();
  const projects = useProjects({ ordering: "-last_activity", page_size: 100 });
  const firstName = user.full_name.split(" ")[0];
  const all = projects.data?.results ?? [];
  const needsAction = all.filter((project) => project.next_step.action_needed);

  return (
    <>
      <header className="mb-6">
        <h1 className="text-2xl text-foreground">Hello, {firstName}</h1>
        <p className="mt-1 text-muted-foreground">
          {user.client
            ? `Projects of ${user.client.company_name}`
            : "Your projects with Five Brothers Solutions"}
        </p>
      </header>

      {projects.isPending && (
        <div aria-hidden="true" className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-52 rounded-lg" />
          <Skeleton className="h-52 rounded-lg" />
        </div>
      )}
      {projects.isError && (
        <Card>
          <ErrorState
            error={projects.error}
            what="your projects"
            onRetry={() => void projects.refetch()}
          />
        </Card>
      )}

      {projects.data && all.length === 0 && (
        <Card>
          <EmptyState
            icon={FolderOpen}
            title="You have no projects yet"
            description="Tell us what you need: a store interior, a display stand, a brand sign, or an event booth."
            action={
              <Button asChild size="lg">
                <Link to="/portal/requests/new">
                  <CirclePlus aria-hidden="true" />
                  Submit your first request
                </Link>
              </Button>
            }
          />
        </Card>
      )}

      {needsAction.length > 0 && (
        <section aria-labelledby="action-heading" className="mb-8">
          <h2 id="action-heading" className="mb-3 text-lg font-semibold text-foreground">
            Action needed
          </h2>
          <ul className="flex flex-col gap-3">
            {needsAction.map((project) => (
              <ActionCard key={project.id} project={project} />
            ))}
          </ul>
        </section>
      )}

      {all.length > 0 && (
        <section aria-labelledby="projects-heading">
          <h2 id="projects-heading" className="mb-3 text-lg font-semibold text-foreground">
            My projects
          </h2>
          <ul className="grid gap-4 md:grid-cols-2">
            {all.map((project) => (
              <li key={project.id}>
                <ProjectCard
                  project={project}
                  to={`/portal/projects/${project.id}`}
                  variant="full"
                  hideClient
                />
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
