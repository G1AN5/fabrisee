import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api, type Paginated, type QueryParams } from "@/lib/api";
import { queryKeys } from "@/lib/query";
import type {
  ProjectCardData,
  ProjectDetail,
  ProjectDocument,
  Quotation,
  Revision,
  Timeline,
} from "@/lib/types";

export interface ProjectListParams extends QueryParams {
  q?: string;
  stage?: string;
  status?: string;
  client?: string;
  project_type?: string;
  needs_action?: string;
  waiting_on?: string;
  overdue?: string;
  due_within?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export function useProjects(params: ProjectListParams, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.projects.list(params),
    queryFn: ({ signal }) => api.get<Paginated<ProjectCardData>>("/projects/", { params, signal }),
    // Keep the rows on screen while the next page or filter loads (no layout jump).
    placeholderData: keepPreviousData,
    enabled: options?.enabled ?? true,
  });
}

export function useProject(projectId: number) {
  return useQuery({
    queryKey: queryKeys.projects.detail(projectId),
    queryFn: ({ signal }) => api.get<ProjectDetail>(`/projects/${projectId}/`, { signal }),
    enabled: Number.isFinite(projectId),
  });
}

export function useProjectTimeline(projectId: number) {
  return useQuery({
    queryKey: queryKeys.projects.timeline(projectId),
    queryFn: ({ signal }) => api.get<Timeline>(`/projects/${projectId}/timeline/`, { signal }),
  });
}

export function useProjectQuotations(projectId: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.projects.quotations(projectId),
    queryFn: ({ signal }) => api.get<Quotation[]>(`/projects/${projectId}/quotations/`, { signal }),
    enabled,
  });
}

export function useProjectRevisions(projectId: number) {
  return useQuery({
    queryKey: queryKeys.projects.revisions(projectId),
    queryFn: ({ signal }) => api.get<Revision[]>(`/projects/${projectId}/revisions/`, { signal }),
  });
}

export function useProjectDocuments(projectId: number) {
  return useQuery({
    queryKey: queryKeys.projects.documents(projectId),
    queryFn: ({ signal }) =>
      api.get<ProjectDocument[]>(`/projects/${projectId}/documents/`, { signal }),
  });
}
