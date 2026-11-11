import { History } from "lucide-react";

import { ActivityFeed } from "@/components/ActivityFeed";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjectTimeline } from "@/features/projects/api";

/** The activity log of a project: who did what and when, newest first. */
export function ActivityTab({ projectId }: { projectId: number }) {
  const timeline = useProjectTimeline(projectId);

  if (timeline.isPending) {
    return (
      <Card className="p-5 sm:p-6">
        <div aria-hidden="true" className="flex flex-col gap-4">
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-10 w-2/3" />
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-10 w-1/2" />
        </div>
      </Card>
    );
  }
  if (timeline.isError) {
    return (
      <Card>
        <ErrorState
          error={timeline.error}
          what="the activity"
          onRetry={() => void timeline.refetch()}
        />
      </Card>
    );
  }
  if (timeline.data.activity.length === 0) {
    return (
      <Card>
        <EmptyState icon={History} title="No activity recorded yet" />
      </Card>
    );
  }
  return (
    <Card className="p-5 sm:p-6">
      <ActivityFeed entries={timeline.data.activity} />
    </Card>
  );
}
