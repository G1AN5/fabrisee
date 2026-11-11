import { useQuery } from "@tanstack/react-query";

import { api, type Paginated } from "@/lib/api";
import { queryKeys } from "@/lib/query";
import type { ClientRecord } from "@/lib/types";

/** All client companies (staff only), for example for the client filter. */
export function useClients(enabled = true) {
  return useQuery({
    queryKey: queryKeys.clients,
    queryFn: ({ signal }) =>
      api.get<Paginated<ClientRecord>>("/clients/", { params: { page_size: 100 }, signal }),
    staleTime: 5 * 60_000,
    enabled,
  });
}
