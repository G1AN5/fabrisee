import { formatMoney } from "@/lib/format";
import { cn } from "@/lib/utils";

/** An amount in Philippine pesos: `₱125,000.00`, with tabular numerals. */
export function Money({ amount, className }: { amount: string | number; className?: string }) {
  return <span className={cn("tabular-nums", className)}>{formatMoney(amount)}</span>;
}
