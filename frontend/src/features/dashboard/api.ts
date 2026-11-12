import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query";
import type { Dashboard, PendingApprovals } from "@/lib/types";

export function useDashboard() {
  return useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: ({ signal }) => api.get<Dashboard>("/dashboard/", { signal }),
    refetchInterval: 5 * 60_000,
  });
}

export function usePendingApprovals() {
  return useQuery({
    queryKey: queryKeys.approvals,
    queryFn: ({ signal }) => api.get<PendingApprovals>("/approvals/pending/", { signal }),
  });
}
