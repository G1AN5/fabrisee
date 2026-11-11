import { Compass, Hammer, LoaderCircle, Lock, ServerCrash } from "lucide-react";
import { isRouteErrorResponse, Link, useRouteError } from "react-router";

import { AppLogo } from "@/components/AppLogo";
import { EmptyState } from "@/components/EmptyState";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";

/** Where "back" leads: the home of the signed-in user, or the sign-in page. */
function useHomePath(): string {
  const { user } = useAuth();
  return user ? user.home_path : "/login";
}

function BackHome() {
  const home = useHomePath();
  return (
    <Button asChild>
      <Link to={home}>{home === "/login" ? "Go to sign in" : "Back to the start page"}</Link>
    </Button>
  );
}

/** 404: the address does not lead anywhere. */
export function NotFoundPage({ what = "page" }: { what?: string }) {
  return (
    <EmptyState
      icon={Compass}
      title={`We could not find this ${what}`}
      description={`The address may be wrong, or the ${what} is not available to you.`}
      action={<BackHome />}
    />
  );
}

/** 403: the user is signed in but this area or function is not for their role. */
export function ForbiddenPage() {
  return (
    <EmptyState
      icon={Lock}
      title="You do not have access to this page"
      description="Your account does not include this area of FabriSee. If you think this is a mistake, ask the administrator."
      action={<BackHome />}
    />
  );
}

/** A screen that belongs to a later milestone of the build. */
export function ComingSoon({
  title,
  milestone,
  children,
}: {
  title: string;
  milestone: string;
  children?: string;
}) {
  return (
    <EmptyState
      icon={Hammer}
      title={`${title} is not built yet`}
      description={
        <>
          {children ? `${children} ` : ""}
          This screen is part of {milestone} of the FabriSee build.
        </>
      }
      action={<BackHome />}
    />
  );
}

/** Shown while FabriSee finds out who is signed in. */
export function LoadingScreen() {
  return (
    <div
      role="status"
      className="flex min-h-dvh flex-col items-center justify-center gap-4 bg-background"
    >
      <AppLogo size="lg" />
      <LoaderCircle className="size-5 animate-spin text-muted-foreground" aria-hidden="true" />
      <span className="sr-only">Loading FabriSee</span>
    </div>
  );
}

/** Shown when the server cannot be reached at all. */
export function ServerUnreachable({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-2 bg-background p-4">
      <AppLogo size="lg" />
      <EmptyState
        icon={ServerCrash}
        title="FabriSee cannot be reached right now"
        description={message}
        action={<Button onClick={onRetry}>Try again</Button>}
      />
    </div>
  );
}

/** Catches errors of a route so one broken screen does not blank the whole app. */
export function RouteError() {
  const error = useRouteError();
  if (isRouteErrorResponse(error) && error.status === 404) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background p-4">
        <NotFoundPage />
      </div>
    );
  }
  console.error(error);
  return (
    <div className="flex min-h-dvh items-center justify-center bg-background p-4">
      <EmptyState
        icon={ServerCrash}
        title="Something went wrong on this page"
        description="Reload the page. If it happens again, tell the administrator what you were doing."
        action={<Button onClick={() => window.location.reload()}>Reload the page</Button>}
      />
    </div>
  );
}
