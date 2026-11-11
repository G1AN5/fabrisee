import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import type { ReactNode } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  cell: (row: T) => ReactNode;
  /** The value of `sort` for this column; a leading "-" means descending. */
  sortKey?: string;
  /** Classes for the cells of the column (width, truncation, alignment). */
  className?: string;
  headerClassName?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  /** A short description of the table for screen readers. */
  caption: string;
  sort?: string;
  onSortChange?: (sort: string) => void;
  onRowClick?: (row: T) => void;
  /** Show skeleton rows instead of data (first load). */
  loading?: boolean;
  skeletonRows?: number;
  /** Shown instead of the table when there are no rows. */
  empty?: ReactNode;
  /** How a row looks as a card on narrow screens (tables become cards). */
  mobileCard?: (row: T) => ReactNode;
  /** Dim the rows while newer data loads. */
  stale?: boolean;
}

function nextSort(current: string | undefined, key: string): string {
  return current === key ? `-${key}` : key;
}

/** A table with sortable headers, loading skeletons, an empty state, and cards on phones. */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  caption,
  sort,
  onSortChange,
  onRowClick,
  loading = false,
  skeletonRows = 6,
  empty,
  mobileCard,
  stale = false,
}: DataTableProps<T>) {
  if (!loading && rows.length === 0 && empty) {
    return <>{empty}</>;
  }

  return (
    <>
      {mobileCard && (
        <ul
          className={cn(
            "flex flex-col gap-3 md:hidden",
            stale && "opacity-60 transition-opacity duration-150",
          )}
        >
          {loading
            ? Array.from({ length: Math.min(skeletonRows, 4) }, (_, index) => (
                <li key={index}>
                  <Skeleton className="h-36 w-full rounded-lg" />
                </li>
              ))
            : rows.map((row) => <li key={rowKey(row)}>{mobileCard(row)}</li>)}
        </ul>
      )}
      <div
        className={cn(
          "overflow-hidden rounded-lg border bg-card shadow-xs",
          mobileCard && "hidden md:block",
        )}
      >
        <Table>
          <caption className="sr-only">{caption}</caption>
          <TableHeader className="sticky top-0 z-10">
            <TableRow>
              {columns.map((column) => {
                const ascending = sort === column.sortKey;
                const descending = sort === `-${column.sortKey}`;
                const sorted = column.sortKey !== undefined && (ascending || descending);
                return (
                  <TableHead
                    key={column.key}
                    className={column.headerClassName}
                    aria-sort={sorted ? (ascending ? "ascending" : "descending") : undefined}
                  >
                    {column.sortKey && onSortChange ? (
                      <button
                        type="button"
                        onClick={() => onSortChange(nextSort(sort, column.sortKey!))}
                        className={cn(
                          "-mx-1 inline-flex items-center gap-1 rounded-sm px-1 py-0.5 text-xs font-medium transition-colors duration-150 hover:text-foreground",
                          sorted ? "text-foreground" : "text-muted-foreground",
                        )}
                      >
                        {column.header}
                        {ascending && <ArrowUp className="size-3.5" aria-hidden="true" />}
                        {descending && <ArrowDown className="size-3.5" aria-hidden="true" />}
                        {!sorted && (
                          <ChevronsUpDown className="size-3.5 opacity-50" aria-hidden="true" />
                        )}
                      </button>
                    ) : (
                      column.header
                    )}
                  </TableHead>
                );
              })}
            </TableRow>
          </TableHeader>
          <TableBody className={cn(stale && "opacity-60 transition-opacity duration-150")}>
            {loading
              ? Array.from({ length: skeletonRows }, (_, index) => (
                  <TableRow key={index}>
                    {columns.map((column) => (
                      <TableCell key={column.key} className={column.className}>
                        <Skeleton className="h-5 w-full max-w-40" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              : rows.map((row) => (
                  <TableRow
                    key={rowKey(row)}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                    className={cn(onRowClick && "cursor-pointer hover:bg-slate-50")}
                  >
                    {columns.map((column) => (
                      <TableCell key={column.key} className={column.className}>
                        {column.cell(row)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
          </TableBody>
        </Table>
      </div>
    </>
  );
}
