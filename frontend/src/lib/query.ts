import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api";

/** Retry only failures that may be temporary (network and server errors), twice at most. */
function shouldRetry(failureCount: number, error: unknown) {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false;
  return failureCount < 2;
}

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: shouldRetry,
        refetchOnWindowFocus: true,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

export const queryClient = createQueryClient();

/** Query keys, one family per resource. Invalidate the family after a mutation. */
export const queryKeys = {
  me: ["auth", "me"] as const,
  privacyNotice: ["auth", "privacy-notice"] as const,
  demoAccounts: ["demo", "accounts"] as const,
  health: ["health"] as const,
  dashboard: ["dashboard"] as const,
  approvals: ["approvals", "pending"] as const,
  clients: ["clients"] as const,
  projects: {
    all: ["projects"] as const,
    list: (params: object) => ["projects", "list", params] as const,
    detail: (id: number) => ["projects", "detail", id] as const,
    timeline: (id: number) => ["projects", "detail", id, "timeline"] as const,
    quotations: (id: number) => ["projects", "detail", id, "quotations"] as const,
    revisions: (id: number) => ["projects", "detail", id, "revisions"] as const,
    documents: (id: number) => ["projects", "detail", id, "documents"] as const,
  },
  notifications: {
    all: ["notifications"] as const,
    list: (params: object) => ["notifications", "list", params] as const,
  },
};
