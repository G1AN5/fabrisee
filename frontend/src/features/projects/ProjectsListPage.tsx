import { FolderSearch, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";

import { type Column, DataTable } from "@/components/DataTable";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { FilterBar, FilterToggle } from "@/components/FilterBar";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { ProjectCard } from "@/components/ProjectCard";
import { ProjectNumber } from "@/components/ProjectNumber";
import { RelativeTime } from "@/components/RelativeTime";
import { StageChip } from "@/components/StageChip";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useClients } from "@/features/clients/api";
import { useProjects } from "@/features/projects/api";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useAuth } from "@/lib/auth";
import { PROJECT_STATUS_LABELS, PROJECT_TYPE_LABELS, STAGES } from "@/lib/constants";
import { describeDue, formatDate } from "@/lib/format";
import type { ProjectCardData } from "@/lib/types";
import { cn } from "@/lib/utils";

const ALL = "all";
const FILTER_KEYS = [
  "q",
  "stage",
  "status",
  "client",
  "project_type",
  "needs_action",
  "waiting_on",
  "overdue",
  "due_within",
] as const;

const SORT_OPTIONS = [
  { value: "-last_activity", label: "Last update, newest first" },
  { value: "target_date", label: "Target date, soonest first" },
  { value: "-target_date", label: "Target date, latest first" },
  { value: "-created", label: "Newest projects first" },
];

const COLUMNS: Column<ProjectCardData>[] = [
  {
    key: "project",
    header: "Project",
    className: "max-w-72",
    cell: (project) => (
      <div className="min-w-0">
        <Link
          to={`/app/projects/${project.id}`}
          onClick={(event) => event.stopPropagation()}
          className="block truncate rounded-sm font-medium text-foreground underline-offset-2 hover:underline"
          title={project.title}
        >
          {project.title}
        </Link>
        <ProjectNumber value={project.project_number} className="text-xs text-muted-foreground" />
      </div>
    ),
  },
  {
    key: "client",
    header: "Client and type",
    className: "max-w-48",
    cell: (project) => (
      <div className="min-w-0">
        <span className="block truncate text-foreground" title={project.client.company_name}>
          {project.client.company_name}
        </span>
        <span className="block truncate text-xs text-muted-foreground">
          {project.project_type_label}
        </span>
      </div>
    ),
  },
  {
    key: "stage",
    header: "Stage",
    cell: (project) => (
      <span className="flex flex-col items-start gap-1">
        <StageChip stage={project.stage} />
        {project.status !== "active" && project.status !== "completed" && (
          <StatusBadge status={project.status} />
        )}
      </span>
    ),
  },
  {
    key: "next_step",
    header: "Next step",
    className: "max-w-80 min-w-48",
    cell: (project) => (
      <span
        className={cn(
          "line-clamp-2",
          project.next_step.action_needed ? "font-medium text-foreground" : "text-slate-700",
        )}
      >
        {project.next_step.text}
      </span>
    ),
  },
  {
    key: "target_date",
    header: "Target date",
    sortKey: "target_date",
    className: "whitespace-nowrap",
    cell: (project) => (
      <span className="flex flex-col">
        <span
          className={cn(
            "tabular-nums",
            project.is_overdue ? "font-medium text-destructive" : "text-foreground",
          )}
        >
          {formatDate(project.target_date)}
        </span>
        {(project.status === "active" || project.status === "on_hold") &&
          project.days_until_target <= 7 && (
            <span
              className={cn(
                "text-xs",
                project.is_overdue ? "text-destructive" : "text-muted-foreground",
              )}
            >
              {describeDue(project.days_until_target)}
            </span>
          )}
      </span>
    ),
  },
  {
    key: "manager",
    header: "Manager",
    className: "max-w-40",
    cell: (project) => (
      <span className="block truncate text-foreground">
        {project.manager?.full_name ?? <span className="text-muted-foreground">Not assigned</span>}
      </span>
    ),
  },
  {
    key: "updated",
    header: "Updated",
    sortKey: "last_activity",
    className: "text-muted-foreground",
    cell: (project) => <RelativeTime value={project.last_activity_at} />,
  },
];

/** The projects list of the staff workspace: a table on desktop, cards on phones. */
export function ProjectsListPage() {
  const { can } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const clients = useClients(can("view_clients"));

  const urlQuery = searchParams.get("q") ?? "";
  const [searchText, setSearchText] = useState(urlQuery);
  const debouncedSearch = useDebouncedValue(searchText.trim(), 300);
  // Typing updates the address after a short pause, so the list can be shared and reloaded.
  useEffect(() => {
    if (debouncedSearch === urlQuery) return;
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (debouncedSearch) next.set("q", debouncedSearch);
        else next.delete("q");
        next.delete("page");
        return next;
      },
      { replace: true },
    );
  }, [debouncedSearch, urlQuery, setSearchParams]);

  function setFilter(key: string, value: string | null) {
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      if (value === null || value === "" || value === ALL) next.delete(key);
      else next.set(key, value);
      next.delete("page");
      return next;
    });
  }

  const ordering = searchParams.get("ordering") ?? "-last_activity";
  const page = Math.max(1, Number(searchParams.get("page")) || 1);
  const params = {
    q: urlQuery || undefined,
    stage: searchParams.get("stage") ?? undefined,
    status: searchParams.get("status") ?? undefined,
    client: searchParams.get("client") ?? undefined,
    project_type: searchParams.get("project_type") ?? undefined,
    needs_action: searchParams.get("needs_action") ?? undefined,
    waiting_on: searchParams.get("waiting_on") ?? undefined,
    overdue: searchParams.get("overdue") ?? undefined,
    due_within: searchParams.get("due_within") ?? undefined,
    ordering,
    page,
  };
  const projects = useProjects(params);
  const filtered = FILTER_KEYS.some((key) => searchParams.has(key));
  const dueWithin = searchParams.get("due_within");

  function clearFilters() {
    setSearchText("");
    setSearchParams((current) => {
      const next = new URLSearchParams();
      const sort = current.get("ordering");
      if (sort) next.set("ordering", sort);
      return next;
    });
  }

  const data = projects.data;

  return (
    <>
      <PageHeader
        title="Projects"
        description={
          data
            ? `${data.count} ${data.count === 1 ? "project" : "projects"}${filtered ? " match the filters" : ""}`
            : "All projects, from request to turnover."
        }
      />

      <FilterBar onClear={filtered ? clearFilters : undefined}>
        <div className="relative w-full sm:w-64">
          <Search
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            type="search"
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            placeholder="Number, title, or client"
            aria-label="Search projects by number, title, or client"
            className="pl-9"
          />
        </div>
        <Select value={params.stage ?? ALL} onValueChange={(value) => setFilter("stage", value)}>
          <SelectTrigger className="w-[calc(50%-0.25rem)] sm:w-44" aria-label="Stage">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All stages</SelectItem>
            {STAGES.map((stage) => (
              <SelectItem key={stage.value} value={stage.value}>
                {stage.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={params.status ?? ALL} onValueChange={(value) => setFilter("status", value)}>
          <SelectTrigger className="w-[calc(50%-0.25rem)] sm:w-36" aria-label="Status">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All statuses</SelectItem>
            {Object.entries(PROJECT_STATUS_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {can("view_clients") && (
          <Select
            value={params.client ?? ALL}
            onValueChange={(value) => setFilter("client", value)}
          >
            <SelectTrigger className="w-[calc(50%-0.25rem)] sm:w-48" aria-label="Client">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>All clients</SelectItem>
              {clients.data?.results.map((client) => (
                <SelectItem key={client.id} value={String(client.id)}>
                  {client.company_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        <Select
          value={params.project_type ?? ALL}
          onValueChange={(value) => setFilter("project_type", value)}
        >
          <SelectTrigger className="w-[calc(50%-0.25rem)] sm:w-40" aria-label="Project type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All types</SelectItem>
            {Object.entries(PROJECT_TYPE_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <FilterToggle
          pressed={params.needs_action === "1"}
          onPressedChange={(pressed) => setFilter("needs_action", pressed ? "1" : null)}
        >
          Needs action
        </FilterToggle>
        <FilterToggle
          pressed={params.waiting_on === "client"}
          onPressedChange={(pressed) => setFilter("waiting_on", pressed ? "client" : null)}
        >
          Waiting for client
        </FilterToggle>
        <FilterToggle
          pressed={params.overdue === "1"}
          onPressedChange={(pressed) => setFilter("overdue", pressed ? "1" : null)}
        >
          Overdue
        </FilterToggle>
        {dueWithin && (
          <FilterToggle pressed onPressedChange={() => setFilter("due_within", null)}>
            Due in the next {dueWithin} days
          </FilterToggle>
        )}
        <div className="w-full sm:ml-auto sm:w-auto">
          <Select value={ordering} onValueChange={(value) => setFilter("ordering", value)}>
            <SelectTrigger className="w-full sm:w-60" aria-label="Sort by">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SORT_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </FilterBar>

      {projects.isError ? (
        <Card>
          <ErrorState
            error={projects.error}
            what="the projects"
            onRetry={() => void projects.refetch()}
          />
        </Card>
      ) : (
        <>
          <DataTable
            caption="Projects"
            columns={COLUMNS}
            rows={data?.results ?? []}
            rowKey={(project) => project.id}
            loading={projects.isPending}
            stale={projects.isPlaceholderData}
            sort={ordering}
            onSortChange={(sort) => setFilter("ordering", sort)}
            onRowClick={(project) => navigate(`/app/projects/${project.id}`)}
            mobileCard={(project) => (
              <ProjectCard project={project} to={`/app/projects/${project.id}`} variant="full" />
            )}
            empty={
              <Card>
                <EmptyState
                  icon={FolderSearch}
                  title={
                    filtered ? "No project matches these filters" : "There are no projects yet"
                  }
                  description={
                    filtered
                      ? "Change or clear the filters to see more projects."
                      : "A project starts when a client submits a request."
                  }
                  action={
                    filtered ? (
                      <Button variant="outline" onClick={clearFilters}>
                        Clear filters
                      </Button>
                    ) : undefined
                  }
                />
              </Card>
            }
          />
          {data && (
            <Pagination
              page={data.page}
              pageSize={data.page_size}
              count={data.count}
              noun="projects"
              onPageChange={(next) =>
                setSearchParams((current) => {
                  const updated = new URLSearchParams(current);
                  if (next <= 1) updated.delete("page");
                  else updated.set("page", String(next));
                  return updated;
                })
              }
            />
          )}
        </>
      )}
    </>
  );
}
