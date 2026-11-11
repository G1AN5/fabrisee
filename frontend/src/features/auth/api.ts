import { useQuery } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api";
import { queryKeys } from "@/lib/query";
import type { DemoAccounts, PrivacyNotice } from "@/lib/types";

export function usePrivacyNotice(enabled = true) {
  return useQuery({
    queryKey: queryKeys.privacyNotice,
    queryFn: ({ signal }) => api.get<PrivacyNotice>("/auth/privacy-notice/", { signal }),
    staleTime: Infinity,
    enabled,
  });
}

/**
 * The demo accounts, when the server offers them (development with demo data).
 * In production the endpoint answers 404 and this returns null.
 */
export function useDemoAccounts() {
  return useQuery({
    queryKey: queryKeys.demoAccounts,
    queryFn: async ({ signal }) => {
      try {
        return await api.get<DemoAccounts>("/demo/accounts/", { signal });
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    staleTime: Infinity,
    retry: false,
  });
}
