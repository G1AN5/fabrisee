import { X } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface FilterBarProps {
  children: ReactNode;
  className?: string;
}

/** The filters above a list: one or more `FilterRow`s. */
export function FilterBar({ children, className }: FilterBarProps) {
  return (
    <div role="search" aria-label="Filters" className={cn("mb-4 flex flex-col gap-2", className)}>
      {children}
    </div>
  );
}

/** One row of filters. Wraps onto more lines on narrow screens. */
export function FilterRow({ children, className }: FilterBarProps) {
  return <div className={cn("flex flex-wrap items-center gap-2", className)}>{children}</div>;
}

interface FilterToggleProps {
  pressed: boolean;
  onPressedChange: (pressed: boolean) => void;
  children: ReactNode;
}

/** An on/off filter such as "Needs action" or "Overdue". */
export function FilterToggle({ pressed, onPressedChange, children }: FilterToggleProps) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={() => onPressedChange(!pressed)}
      className={cn(
        "inline-flex h-(--control-h) items-center gap-1.5 rounded-md border px-3 text-sm font-medium whitespace-nowrap shadow-xs transition-colors duration-150 ease-out",
        pressed
          ? "border-primary bg-status-sent-bg text-primary"
          : "border-input bg-card text-foreground hover:bg-accent",
      )}
    >
      {children}
    </button>
  );
}

/** Removes every filter at once. Show it only while a filter is set. */
export function ClearFilters({ onClear }: { onClear: () => void }) {
  return (
    <Button variant="ghost" onClick={onClear} className="text-muted-foreground">
      <X aria-hidden="true" />
      Clear filters
    </Button>
  );
}
