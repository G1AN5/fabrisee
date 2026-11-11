import { useQuery } from "@tanstack/react-query";
import { CircleAlert, CircleCheck, RefreshCw } from "lucide-react";

import { AppLogo } from "@/components/AppLogo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";

interface Health {
  status: string;
  service: string;
  version: string;
  database: string;
  time: string;
  time_zone: string;
}

/** Milestone 0 placeholder: shows that the React app, the proxy and the API work together. */
export function FoundationPage() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => api.get<Health>("/health/", { signal }),
    retry: false,
  });

  return (
    <main className="mx-auto flex min-h-dvh max-w-xl flex-col justify-center gap-6 p-4 sm:p-6">
      <AppLogo size="lg" />
      <div>
        <h1 className="text-2xl">The foundation is ready</h1>
        <p className="mt-2 text-muted-foreground">
          Client coordination for custom fabrication projects. This page checks that the React app
          can reach the FabriSee API.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>API status</CardTitle>
          <CardDescription>GET /api/health/</CardDescription>
        </CardHeader>
        <CardContent>
          {health.isPending && <Skeleton className="h-12 w-full" />}
          {health.isError && (
            <div className="flex flex-col gap-3" role="alert">
              <p className="flex items-start gap-2 text-destructive">
                <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
                <span>{health.error.message}</span>
              </p>
              <Button variant="outline" className="w-fit" onClick={() => health.refetch()}>
                <RefreshCw aria-hidden="true" />
                Try again
              </Button>
            </div>
          )}
          {health.isSuccess && (
            <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2">
              <dt className="text-muted-foreground">Status</dt>
              <dd className="flex items-center gap-1.5 font-medium text-status-approved">
                <CircleCheck className="size-4" aria-hidden="true" />
                Connected
              </dd>
              <dt className="text-muted-foreground">Database</dt>
              <dd>{health.data.database}</dd>
              <dt className="text-muted-foreground">Version</dt>
              <dd className="tabular-nums">{health.data.version}</dd>
              <dt className="text-muted-foreground">Server time</dt>
              <dd className="tabular-nums">
                {health.data.time} ({health.data.time_zone})
              </dd>
            </dl>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
