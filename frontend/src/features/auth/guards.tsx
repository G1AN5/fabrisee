import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";

import { ForbiddenPage, LoadingScreen, ServerUnreachable } from "@/components/StatusPages";
import { PrivacyNoticeDialog } from "@/features/auth/PrivacyNoticeDialog";
import { useAuth } from "@/lib/auth";
import type { Permission } from "@/lib/types";

interface RequireAreaProps {
  /** `staff`: the staff workspace (/app). `portal`: the client portal (/portal). */
  area: "staff" | "portal";
  children: ReactNode;
}

/**
 * Lets only signed-in users of the right area through (process rule PR9 in the UI; the
 * API enforces it for the data). Nobody signed in: go to the sign-in page and come back
 * afterwards. Wrong area: a "no access" page with a way back.
 */
export function RequireArea({ area, children }: RequireAreaProps) {
  const { status, user, error, retry, signedOutByUser } = useAuth();
  const location = useLocation();

  if (status === "loading") return <LoadingScreen />;
  if (status === "unreachable") {
    return (
      <ServerUnreachable
        message={error?.message ?? "Check your connection and try again."}
        onRetry={retry}
      />
    );
  }
  if (!user) {
    // After "Sign out" the sign-in page starts fresh. A session that ended by itself, or a
    // link opened without one, comes back to this page after signing in.
    if (signedOutByUser) return <Navigate to="/login" replace />;
    const next = `${location.pathname}${location.search}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }

  const allowed = area === "staff" ? user.is_company_staff : !user.is_company_staff;
  if (!allowed) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background p-4">
        <ForbiddenPage />
      </div>
    );
  }

  return (
    <>
      {children}
      <PrivacyNoticeDialog open={user.privacy_acknowledged_at === null} mode="acknowledge" />
    </>
  );
}

/** Shows the page only when the user's role has the permission; otherwise "no access". */
export function RequirePermission({
  permission,
  children,
}: {
  permission: Permission;
  children: ReactNode;
}) {
  const { can } = useAuth();
  return can(permission) ? <>{children}</> : <ForbiddenPage />;
}

/** `/`: send everybody to the start page of their area, or to the sign-in page. */
export function HomeRedirect() {
  const { status, user, error, retry } = useAuth();
  if (status === "loading") return <LoadingScreen />;
  if (status === "unreachable") {
    return (
      <ServerUnreachable
        message={error?.message ?? "Check your connection and try again."}
        onRetry={retry}
      />
    );
  }
  return <Navigate to={user ? user.home_path : "/login"} replace />;
}
