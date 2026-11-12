import { Bell, CirclePlus, FolderOpen, type LucideIcon } from "lucide-react";
import { Link, NavLink, Outlet } from "react-router";

import { AppLogo } from "@/components/AppLogo";
import { NotificationBell } from "@/components/NotificationBell";
import { Button } from "@/components/ui/button";
import { UserMenu } from "@/components/UserMenu";
import { useNotifications } from "@/features/notifications/api";
import { useUiScale } from "@/hooks/useUiScale";
import { badgeCount } from "@/lib/format";
import { cn } from "@/lib/utils";

interface PortalNavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

const NAV: PortalNavItem[] = [
  { to: "/portal", label: "My projects", icon: FolderOpen, end: true },
  { to: "/portal/requests/new", label: "New request", icon: CirclePlus },
  { to: "/portal/notifications", label: "Notifications", icon: Bell },
];

/**
 * The client portal: a top bar with the wordmark, "My projects", "New request", the
 * notification bell, and the user menu; on phones a bottom navigation bar. Larger text
 * and taller controls than the staff workspace, because clients approve on phones.
 */
export function PortalLayout() {
  useUiScale("portal");
  const unread = useNotifications({ page_size: 10 }, { poll: true }).data?.unread_count ?? 0;

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <a
        href="#main"
        className="sr-only z-50 rounded-md bg-card px-3 py-2 font-medium text-foreground shadow-lg focus:not-sr-only focus:fixed focus:top-2 focus:left-2"
      >
        Skip to the content
      </a>

      <header className="sticky top-0 z-30 border-b bg-card/95 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-5xl items-center gap-6 px-4">
          <Link to="/portal" className="rounded-sm" aria-label="FabriSee, my projects">
            <AppLogo />
          </Link>
          <nav aria-label="Client portal" className="hidden items-center gap-1 md:flex">
            {NAV.slice(0, 1).map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "rounded-md px-3 py-2 text-sm font-medium transition-colors duration-150 ease-out",
                    isActive
                      ? "bg-status-sent-bg text-primary"
                      : "text-slate-700 hover:bg-accent hover:text-foreground",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <Button asChild className="hidden md:inline-flex">
              <Link to="/portal/requests/new">
                <CirclePlus aria-hidden="true" />
                New request
              </Link>
            </Button>
            <NotificationBell allHref="/portal/notifications" className="hidden md:inline-flex" />
            <UserMenu />
          </div>
        </div>
      </header>

      <main id="main" tabIndex={-1} className="flex-1 outline-none">
        <div className="mx-auto max-w-5xl px-4 pt-6 pb-28 md:pb-12">
          <Outlet />
        </div>
      </main>

      <nav
        aria-label="Client portal"
        className="fixed inset-x-0 bottom-0 z-30 border-t bg-card pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        <ul className="mx-auto grid max-w-md grid-cols-3">
          {NAV.map((item) => {
            const Icon = item.icon;
            const showBadge = item.to === "/portal/notifications" && unread > 0;
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    cn(
                      "flex min-h-16 flex-col items-center justify-center gap-1 px-2 text-xs font-medium transition-colors duration-150 ease-out -outline-offset-2",
                      isActive ? "text-primary" : "text-slate-600",
                    )
                  }
                >
                  <span className="relative">
                    <Icon className="size-6" aria-hidden="true" />
                    {showBadge && (
                      <span
                        aria-hidden="true"
                        className="absolute -top-1 -right-2 flex h-4.5 min-w-4.5 items-center justify-center rounded-full bg-destructive px-1 text-[0.6875rem] leading-none font-semibold text-white"
                      >
                        {badgeCount(unread)}
                      </span>
                    )}
                  </span>
                  <span>
                    {item.label}
                    {showBadge && <span className="sr-only">, {unread} unread</span>}
                  </span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
