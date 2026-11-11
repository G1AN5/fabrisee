import { Menu, Plus } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router";

import { AppLogo } from "@/components/AppLogo";
import { NotificationBell } from "@/components/NotificationBell";
import { SearchCommand } from "@/components/SearchCommand";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import { UserMenu } from "@/components/UserMenu";
import { useNotifications } from "@/features/notifications/api";
import { useUiScale } from "@/hooks/useUiScale";
import { type NavItem, visibleNavItems } from "@/layouts/staffNav";
import { useAuth, useCurrentUser } from "@/lib/auth";
import { badgeCount } from "@/lib/format";
import { cn } from "@/lib/utils";

function SidebarLink({
  item,
  badge,
  onNavigate,
}: {
  item: NavItem;
  badge?: number;
  onNavigate?: () => void;
}) {
  const Icon = item.icon;
  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "relative flex min-h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors duration-150 ease-out -outline-offset-2",
          isActive
            ? "bg-sidebar-active text-sidebar-active-foreground before:absolute before:inset-y-1.5 before:left-0 before:w-[3px] before:rounded-full before:bg-sidebar-indicator"
            : "text-sidebar-foreground hover:bg-sidebar-active/60 hover:text-white",
        )
      }
    >
      <Icon className="size-4 shrink-0" aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate">{item.label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="rounded-full bg-sidebar-indicator px-1.5 py-0.5 text-[0.6875rem] leading-none font-semibold text-white">
          <span aria-hidden="true">{badgeCount(badge)}</span>
          <span className="sr-only">{badge} unread</span>
        </span>
      )}
    </NavLink>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const user = useCurrentUser();
  const unread = useNotifications({ page_size: 10 }, { poll: true }).data?.unread_count;
  const items = visibleNavItems(user.permissions);
  const main = items.filter((item) => !item.admin);
  const admin = items.filter((item) => item.admin);

  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 shrink-0 items-center px-5">
        <Link to="/app" onClick={onNavigate} className="rounded-sm" aria-label="FabriSee dashboard">
          <AppLogo variant="inverse" />
        </Link>
      </div>
      <nav aria-label="Staff workspace" className="flex-1 overflow-y-auto px-3 py-2">
        <ul className="flex flex-col gap-0.5">
          {main.map((item) => (
            <li key={item.to}>
              <SidebarLink
                item={item}
                onNavigate={onNavigate}
                badge={item.to === "/app/notifications" ? unread : undefined}
              />
            </li>
          ))}
        </ul>
        {admin.length > 0 && (
          <>
            <p className="mt-6 mb-1 px-3 text-xs font-medium text-sidebar-muted">Administration</p>
            <ul className="flex flex-col gap-0.5">
              {admin.map((item) => (
                <li key={item.to}>
                  <SidebarLink item={item} onNavigate={onNavigate} />
                </li>
              ))}
            </ul>
          </>
        )}
      </nav>
      <div className="shrink-0 border-t border-sidebar-border p-3">
        <UserMenu variant="sidebar" />
      </div>
    </div>
  );
}

/**
 * The staff workspace: a dark sidebar with the navigation and the user menu, and a top
 * bar with the global search, "New request", and the notification bell. On small screens
 * the sidebar becomes a slide-over menu.
 */
export function StaffLayout() {
  useUiScale("staff");
  const { can } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-dvh bg-background">
      <a
        href="#main"
        className="sr-only z-50 rounded-md bg-card px-3 py-2 font-medium text-foreground shadow-lg focus:not-sr-only focus:fixed focus:top-2 focus:left-2"
      >
        Skip to the content
      </a>

      <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 lg:block">
        <SidebarContent />
      </aside>

      <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
        <SheetContent
          side="left"
          className="border-sidebar-border bg-sidebar p-0"
          closeClassName="text-sidebar-foreground hover:bg-sidebar-active hover:text-white"
        >
          <SheetTitle className="sr-only">Menu</SheetTitle>
          <SheetDescription className="sr-only">Navigation of the staff workspace</SheetDescription>
          <SidebarContent onNavigate={() => setMenuOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex min-h-dvh min-w-0 flex-col lg:pl-60">
        <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-2 border-b bg-card/95 px-4 backdrop-blur-sm sm:gap-3 lg:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="-ml-2 lg:hidden"
            aria-label="Open the menu"
            onClick={() => setMenuOpen(true)}
          >
            <Menu className="size-5" aria-hidden="true" />
          </Button>
          <SearchCommand className="max-w-md flex-1" />
          <div className="ml-auto flex shrink-0 items-center gap-1 sm:gap-2">
            {can("submit_request") && (
              <Button asChild>
                <Link to="/app/requests/new" aria-label="New request">
                  <Plus aria-hidden="true" />
                  <span className="hidden sm:inline" aria-hidden="true">
                    New request
                  </span>
                </Link>
              </Button>
            )}
            <NotificationBell allHref="/app/notifications" />
          </div>
        </header>
        <main id="main" tabIndex={-1} className="flex-1 px-4 py-6 outline-none lg:px-6">
          <div className="mx-auto max-w-[1280px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
