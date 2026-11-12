import { cn } from "@/lib/utils";

/** A project number such as `FS-2026-0007`, in an even, tabular style. */
export function ProjectNumber({ value, className }: { value: string; className?: string }) {
  return (
    <span className={cn("font-medium tracking-tight whitespace-nowrap tabular-nums", className)}>
      {value}
    </span>
  );
}
