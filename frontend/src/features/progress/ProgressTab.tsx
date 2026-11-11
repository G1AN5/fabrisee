import { Milestone } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { Timeline, type TimelineItem } from "@/components/Timeline";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjectTimeline } from "@/features/projects/api";
import { stageInfo } from "@/lib/constants";
import { formatDateTime } from "@/lib/format";
import type { StageUpdate } from "@/lib/types";
import { cn } from "@/lib/utils";

function toItem(update: StageUpdate, forClient: boolean): TimelineItem {
  const info = stageInfo(update.to_stage);
  const who = update.updated_by?.full_name;
  const parts = [formatDateTime(update.created_at)];
  if (who) parts.unshift(who);
  // Staff also see how the change came about: a process rule, a manual update, an override.
  if (!forClient) parts.push(update.source_label);
  return {
    id: update.id,
    icon: info.icon,
    iconClassName: cn("border", info.chip),
    title: update.text,
    meta: parts.join(" · "),
    body: update.remarks ? (
      <p className="rounded-md bg-slate-50 px-3 py-2 text-foreground">{update.remarks}</p>
    ) : undefined,
  };
}

interface ProgressTabProps {
  projectId: number;
  /** Plain-language wording for the client portal. */
  forClient?: boolean;
}

/**
 * The progress of a project: every stage change with who made it and when (PR7), newest
 * first. Changes made by the process rules (PR3, PR5) are part of the same timeline.
 */
export function ProgressTab({ projectId, forClient = false }: ProgressTabProps) {
  const timeline = useProjectTimeline(projectId);

  if (timeline.isPending) {
    return (
      <Card className="p-5 sm:p-6">
        <div aria-hidden="true" className="flex flex-col gap-6">
          <Skeleton className="h-12 w-3/4" />
          <Skeleton className="h-12 w-2/3" />
          <Skeleton className="h-12 w-3/4" />
        </div>
      </Card>
    );
  }
  if (timeline.isError) {
    return (
      <Card>
        <ErrorState
          error={timeline.error}
          what="the progress"
          onRetry={() => void timeline.refetch()}
        />
      </Card>
    );
  }
  const updates = [...timeline.data.stage_updates].reverse();
  if (updates.length === 0) {
    return (
      <Card>
        <EmptyState icon={Milestone} title="No progress recorded yet" />
      </Card>
    );
  }
  return (
    <Card className="p-5 sm:p-6">
      <Timeline items={updates.map((update) => toItem(update, forClient))} />
    </Card>
  );
}
