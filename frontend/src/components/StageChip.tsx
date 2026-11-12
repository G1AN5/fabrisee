import { stageInfo } from "@/lib/constants";
import type { Stage } from "@/lib/types";
import { cn } from "@/lib/utils";

interface StageChipProps {
  stage: Stage;
  /** Use the shorter label ("Delivery") where space is tight. */
  short?: boolean;
  className?: string;
}

/** The stage of a project: always the stage name with its color and icon, never color alone. */
export function StageChip({ stage, short = false, className }: StageChipProps) {
  const info = stageInfo(stage);
  const Icon = info.icon;
  return (
    <span
      className={cn(
        "inline-flex w-fit shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        info.chip,
        className,
      )}
    >
      <Icon className="size-3.5 shrink-0" aria-hidden="true" />
      {short ? (
        <>
          <span aria-hidden="true">{info.shortLabel}</span>
          <span className="sr-only">{info.label}</span>
        </>
      ) : (
        info.label
      )}
    </span>
  );
}
