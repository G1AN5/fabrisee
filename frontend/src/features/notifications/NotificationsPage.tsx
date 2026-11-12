import { BellOff, CheckCheck } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { FilterBar, FilterRow, FilterToggle } from "@/components/FilterBar";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { ProjectNumber } from "@/components/ProjectNumber";
import { RelativeTime } from "@/components/RelativeTime";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from "@/features/notifications/api";
import type { AppNotification } from "@/lib/types";
import { cn } from "@/lib/utils";

/** All notifications of the signed-in user (staff workspace and client portal). */
export function NotificationsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const unreadOnly = searchParams.get("unread") === "1";
  const page = Math.max(1, Number(searchParams.get("page")) || 1);
  const notifications = useNotifications({ unread: unreadOnly ? "1" : undefined, page });
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();
  const data = notifications.data;
  const unread = data?.unread_count ?? 0;

  function open(notification: AppNotification) {
    if (!notification.is_read) markRead.mutate(notification.id);
    if (notification.link) navigate(notification.link);
  }

  return (
    <>
      <PageHeader
        title="Notifications"
        description={
          data
            ? unread === 0
              ? "You have read everything."
              : `${unread} unread ${unread === 1 ? "notification" : "notifications"}`
            : undefined
        }
        actions={
          <Button
            variant="outline"
            disabled={unread === 0 || markAll.isPending}
            onClick={() => markAll.mutate()}
          >
            <CheckCheck aria-hidden="true" />
            Mark all as read
          </Button>
        }
      />

      <FilterBar>
        <FilterRow>
          <FilterToggle
            pressed={unreadOnly}
            onPressedChange={(pressed) =>
              setSearchParams(pressed ? { unread: "1" } : {}, { replace: true })
            }
          >
            Unread only
          </FilterToggle>
        </FilterRow>
      </FilterBar>

      <Card className="overflow-hidden">
        {notifications.isPending && (
          <div aria-hidden="true" className="flex flex-col gap-4 p-5">
            {Array.from({ length: 5 }, (_, index) => (
              <Skeleton key={index} className="h-14 w-full" />
            ))}
          </div>
        )}
        {notifications.isError && (
          <ErrorState
            error={notifications.error}
            what="your notifications"
            onRetry={() => void notifications.refetch()}
          />
        )}
        {data && data.results.length === 0 && (
          <EmptyState
            icon={BellOff}
            title={unreadOnly ? "No unread notifications" : "You have no notifications yet"}
            description="FabriSee tells you here when a quotation, a design revision, or a stage change needs your attention."
          />
        )}
        {data && data.results.length > 0 && (
          <ul className={cn("divide-y", notifications.isPlaceholderData && "opacity-60")}>
            {data.results.map((notification) => (
              <li key={notification.id}>
                <button
                  type="button"
                  onClick={() => open(notification)}
                  className="flex w-full items-start gap-3 px-5 py-4 text-left transition-colors duration-150 -outline-offset-2 hover:bg-slate-50 sm:px-6"
                >
                  <span
                    aria-hidden="true"
                    className={cn(
                      "mt-2 size-2 shrink-0 rounded-full",
                      notification.is_read ? "bg-transparent" : "bg-primary",
                    )}
                  />
                  <span className="min-w-0 flex-1">
                    <span
                      className={cn(
                        "block text-foreground",
                        !notification.is_read && "font-semibold",
                      )}
                    >
                      {!notification.is_read && <span className="sr-only">Unread: </span>}
                      {notification.title}
                    </span>
                    {notification.message && (
                      <span className="mt-0.5 block text-muted-foreground">
                        {notification.message}
                      </span>
                    )}
                    <span className="mt-1 flex flex-wrap gap-x-2 text-xs text-muted-foreground">
                      {notification.project && (
                        <>
                          <ProjectNumber value={notification.project.project_number} />
                          <span className="max-w-full truncate">{notification.project.title}</span>
                        </>
                      )}
                      <RelativeTime value={notification.created_at} />
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {data && (
        <Pagination
          page={data.page}
          pageSize={data.page_size}
          count={data.count}
          noun="notifications"
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
  );
}
