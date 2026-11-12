import { Bell, CheckCheck } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { RelativeTime } from "@/components/RelativeTime";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from "@/features/notifications/api";
import { badgeCount } from "@/lib/format";
import type { AppNotification } from "@/lib/types";
import { cn } from "@/lib/utils";

interface NotificationBellProps {
  /** Where "View all" leads: the notifications page of the current area. */
  allHref: string;
  /** Use on dark surfaces. */
  className?: string;
}

/** The bell with the unread count; opens the latest ten notifications. */
export function NotificationBell({ allHref, className }: NotificationBellProps) {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const latest = useNotifications({ page_size: 10 }, { poll: true });
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();
  const unread = latest.data?.unread_count ?? 0;

  function openNotification(notification: AppNotification) {
    if (!notification.is_read) markRead.mutate(notification.id);
    setOpen(false);
    if (notification.link) navigate(notification.link);
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn("relative", className)}
          aria-label={unread > 0 ? `Notifications, ${unread} unread` : "Notifications"}
        >
          <Bell className="size-5" aria-hidden="true" />
          {unread > 0 && (
            <span
              aria-hidden="true"
              className="absolute top-0.5 right-0.5 flex h-4.5 min-w-4.5 items-center justify-center rounded-full bg-destructive px-1 text-[0.6875rem] leading-none font-semibold text-white"
            >
              {badgeCount(unread)}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-96 p-0">
        <div className="flex items-center justify-between gap-2 border-b px-4 py-3">
          <h2 className="text-sm font-semibold">Notifications</h2>
          <Button
            variant="ghost"
            size="sm"
            disabled={unread === 0 || markAll.isPending}
            onClick={() => markAll.mutate()}
            className="-mr-2 text-muted-foreground"
          >
            <CheckCheck aria-hidden="true" />
            Mark all as read
          </Button>
        </div>
        <div className="max-h-[min(26rem,60dvh)] overflow-y-auto">
          {latest.isPending && (
            <div className="flex flex-col gap-3 p-4">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          )}
          {latest.isError && (
            <p role="alert" className="px-4 py-8 text-center text-muted-foreground">
              Notifications could not be loaded.
            </p>
          )}
          {latest.data && latest.data.results.length === 0 && (
            <p className="px-4 py-8 text-center text-muted-foreground">
              You have no notifications yet.
            </p>
          )}
          {latest.data && latest.data.results.length > 0 && (
            <ul className="divide-y">
              {latest.data.results.map((notification) => (
                <li key={notification.id}>
                  <button
                    type="button"
                    onClick={() => openNotification(notification)}
                    className="flex w-full gap-3 px-4 py-3 text-left transition-colors duration-150 -outline-offset-2 hover:bg-accent"
                  >
                    <span
                      aria-hidden="true"
                      className={cn(
                        "mt-1.5 size-2 shrink-0 rounded-full",
                        notification.is_read ? "bg-transparent" : "bg-primary",
                      )}
                    />
                    <span className="min-w-0 flex-1">
                      <span
                        className={cn(
                          "block text-foreground",
                          !notification.is_read && "font-medium",
                        )}
                      >
                        {!notification.is_read && <span className="sr-only">Unread: </span>}
                        {notification.title}
                      </span>
                      <span className="mt-0.5 flex flex-wrap gap-x-2 text-xs text-muted-foreground">
                        {notification.project && (
                          <span className="tabular-nums">
                            {notification.project.project_number}
                          </span>
                        )}
                        <RelativeTime value={notification.created_at} />
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="border-t p-2">
          <Button asChild variant="ghost" className="w-full" onClick={() => setOpen(false)}>
            <Link to={allHref}>View all notifications</Link>
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
