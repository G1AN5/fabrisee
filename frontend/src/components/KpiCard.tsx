import { ArrowRight, type LucideIcon } from "lucide-react";
import { Link } from "react-router";

import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: number;
  /** A short line under the number, for example "2 decisions · 1 project". */
  hint?: string;
  icon: LucideIcon;
  /** The filtered list this number comes from. */
  to: string;
  /** Draw attention (red number) when the value is above zero. */
  alert?: boolean;
}

/** A key number of the dashboard. The whole card links to the list behind it. */
export function KpiCard({ label, value, hint, icon: Icon, to, alert = false }: KpiCardProps) {
  const alerting = alert && value > 0;
  return (
    <Link
      to={to}
      className="group flex flex-col gap-2 rounded-lg border bg-card p-4 shadow-xs sm:p-5 transition-[border-color,box-shadow] duration-150 ease-out hover:border-slate-300 hover:shadow-sm"
    >
      <span className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-muted-foreground">{label}</span>
        <span
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-md",
            alerting ? "bg-status-changes-bg text-status-changes" : "bg-muted text-slate-600",
          )}
        >
          <Icon className="size-4" aria-hidden="true" />
        </span>
      </span>
      <span
        className={cn(
          "text-3xl font-bold tabular-nums",
          alerting ? "text-destructive" : "text-foreground",
        )}
      >
        {value}
      </span>
      <span className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
        <span className="line-clamp-2">{hint}</span>
        <ArrowRight
          className="size-3.5 shrink-0 opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-visible:opacity-100"
          aria-hidden="true"
        />
      </span>
    </Link>
  );
}
