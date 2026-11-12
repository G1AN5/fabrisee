import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

interface PaginationProps {
  page: number;
  pageSize: number;
  count: number;
  onPageChange: (page: number) => void;
  /** What is listed, for example "projects". */
  noun: string;
}

/** "Showing 1 to 20 of 23 projects" with Previous and Next. */
export function Pagination({ page, pageSize, count, onPageChange, noun }: PaginationProps) {
  if (count === 0) return null;
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  const first = (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, count);
  return (
    <nav
      aria-label="Pages"
      className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground"
    >
      <p className="tabular-nums">
        Showing {first} to {last} of {count} {noun}
      </p>
      {totalPages > 1 && (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft aria-hidden="true" />
            Previous
          </Button>
          <span className="tabular-nums">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Next
            <ChevronRight aria-hidden="true" />
          </Button>
        </div>
      )}
    </nav>
  );
}
