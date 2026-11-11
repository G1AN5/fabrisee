import { Check } from "lucide-react";

import { STAGES, stageIndex, stageInfo, type StepState, stepState } from "@/lib/constants";
import { formatShortDate } from "@/lib/format";
import type { ProjectStatus, Stage, StageDates } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATE_TEXT: Record<StepState, string> = {
  done: "completed",
  current: "current stage",
  upcoming: "not started",
};

interface StageTrackerProps {
  stage: Stage;
  /** When the project entered each stage it has reached. */
  stageDates?: StageDates;
  status?: ProjectStatus;
  /** `auto`: a row from the `sm` breakpoint up, a column on phones. */
  orientation?: "auto" | "horizontal" | "vertical";
  className?: string;
}

/**
 * The five stages of a project with the current one marked, each with its icon, name,
 * and the date the project entered it. Request → Design → Production → Delivery and
 * Installation → Turnover.
 */
export function StageTracker({
  stage,
  stageDates,
  status,
  orientation = "auto",
  className,
}: StageTrackerProps) {
  const row = orientation === "horizontal";
  const column = orientation === "vertical";
  const auto = orientation === "auto";
  const inactive = status === "cancelled" || status === "on_hold";

  return (
    <ol
      aria-label="Project stages"
      className={cn(
        "flex",
        row && "flex-row",
        column && "flex-col",
        auto && "flex-col sm:flex-row",
        inactive && "opacity-60",
        className,
      )}
    >
      {STAGES.map((info, index) => {
        const state = stepState(info.value, stage, status);
        const Icon = state === "done" ? Check : info.icon;
        const date = stageDates?.[info.value];
        const reached = state !== "upcoming";
        const last = index === STAGES.length - 1;
        return (
          <li
            key={info.value}
            aria-current={state === "current" ? "step" : undefined}
            className={cn(
              "relative flex min-w-0",
              row && "flex-1 flex-col items-center text-center",
              column && "gap-3 pb-5 last:pb-0",
              auto &&
                "gap-3 pb-5 last:pb-0 sm:flex-1 sm:flex-col sm:items-center sm:gap-0 sm:pb-0 sm:text-center",
            )}
          >
            {/* Connector to the next stage: a row line or a column line. */}
            {!last && (
              <span
                aria-hidden="true"
                className={cn(
                  "absolute",
                  stepState(STAGES[index + 1]!.value, stage, status) === "upcoming"
                    ? "bg-slate-200"
                    : "bg-slate-400",
                  row && "top-[17px] left-1/2 h-0.5 w-full",
                  column && "top-9 bottom-0 left-[17px] w-0.5",
                  auto &&
                    "top-9 bottom-0 left-[17px] w-0.5 sm:top-[17px] sm:bottom-auto sm:left-1/2 sm:h-0.5 sm:w-full",
                )}
              />
            )}
            <span
              className={cn(
                "relative z-10 flex size-9 shrink-0 items-center justify-center rounded-full border-2",
                state === "current" && stageInfo(info.value).solid,
                state === "done" && cn("bg-card", info.text, "border-current"),
                state === "upcoming" && "border-slate-300 bg-card text-slate-400",
              )}
            >
              <Icon className="size-4" aria-hidden="true" />
            </span>
            <span
              className={cn(
                "flex min-w-0 flex-col",
                row && "mt-2 px-1",
                column && "pt-1.5",
                auto && "pt-1.5 sm:mt-2 sm:px-1 sm:pt-0",
              )}
            >
              <span
                className={cn(
                  "text-xs leading-tight",
                  state === "current" && cn("font-semibold", info.text),
                  state === "done" && "font-medium text-foreground",
                  state === "upcoming" && "font-medium text-muted-foreground",
                )}
              >
                {info.label}
                <span className="sr-only"> ({STATE_TEXT[state]})</span>
              </span>
              <span className="mt-0.5 min-h-4 text-xs text-muted-foreground tabular-nums">
                {reached && date ? formatShortDate(date) : ""}
              </span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}

/** The stage as five small segments with its name: for cards, where space is tight. */
export function StageSteps({ stage, status }: { stage: Stage; status?: ProjectStatus }) {
  const current = stageIndex(stage);
  const info = stageInfo(stage);
  return (
    <div
      role="img"
      aria-label={`Stage ${current + 1} of ${STAGES.length}: ${info.label}`}
      className="flex items-center gap-1"
    >
      {STAGES.map((item) => {
        const state = stepState(item.value, stage, status);
        return (
          <span
            key={item.value}
            className={cn(
              "h-1.5 flex-1 rounded-full",
              state === "upcoming" ? "bg-slate-200" : "",
              state === "done" && "bg-slate-400",
              state === "current" && item.solid,
            )}
          />
        );
      })}
    </div>
  );
}
