import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type Paginated, type QueryParams } from "@/lib/api";
import { queryKeys } from "@/lib/query";
import type { AppNotification } from "@/lib/types";

export interface NotificationPage extends Paginated<AppNotification> {
  unread_count: number;
}

export interface NotificationParams extends QueryParams {
  unread?: string;
  category?: string;
  event?: string;
  page?: number;
  page_size?: number;
}

export function useNotifications(params: NotificationParams, options?: { poll?: boolean }) {
  return useQuery({
    queryKey: queryKeys.notifications.list(params),
    queryFn: ({ signal }) => api.get<NotificationPage>("/notifications/", { params, signal }),
    placeholderData: keepPreviousData,
    // The bell checks for new notifications once a minute.
    refetchInterval: options?.poll ? 60_000 : false,
  });
}

/**
 * Marks one notification as read. This is the only optimistic update in FabriSee:
 * the unread dot and the count change at once, and are restored if the request fails.
 */
export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.post<{ unread_count: number }>(`/notifications/${id}/read/`),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.notifications.all });
      const previous = queryClient.getQueriesData<NotificationPage>({
        queryKey: queryKeys.notifications.all,
      });
      queryClient.setQueriesData<NotificationPage>(
        { queryKey: queryKeys.notifications.all },
        (page) => {
          if (!page) return page;
          const target = page.results.find((item) => item.id === id);
          const wasUnread = target ? !target.is_read : false;
          return {
            ...page,
            unread_count: Math.max(0, page.unread_count - (wasUnread ? 1 : 0)),
            results: page.results.map((item) =>
              item.id === id ? { ...item, is_read: true } : item,
            ),
          };
        },
      );
      return { previous };
    },
    onError: (_error, _id, context) => {
      for (const [key, data] of context?.previous ?? []) queryClient.setQueryData(key, data);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all }),
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ marked: number }>("/notifications/read-all/"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all }),
  });
}
