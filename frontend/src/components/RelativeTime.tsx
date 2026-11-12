import { useNow } from "@/hooks/useNow";
import { formatDateTime, formatRelative } from "@/lib/format";
import { cn } from "@/lib/utils";

interface RelativeTimeProps {
  value: string;
  className?: string;
}

/**
 * "2 days ago" within the last seven days, the date after that. The exact date and time
 * are in the tooltip and in the `datetime` attribute.
 */
export function RelativeTime({ value, className }: RelativeTimeProps) {
  const now = useNow();
  return (
    <time
      dateTime={value}
      title={formatDateTime(value)}
      className={cn("whitespace-nowrap tabular-nums", className)}
    >
      {formatRelative(value, new Date(now))}
    </time>
  );
}
