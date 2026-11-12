/**
 * Dates, money, and sizes, formatted the same way everywhere (build guide, 11.7).
 * All times are shown in Manila time, whatever the time zone of the device.
 */
import { TZDate } from "@date-fns/tz";
import { differenceInCalendarDays, format, formatDistanceStrict } from "date-fns";

export const TIME_ZONE = "Asia/Manila";

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;
const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;

type DateInput = string | Date;

/** The moment or calendar date as a date in Manila time. */
function manila(value: DateInput): TZDate {
  if (typeof value === "string") {
    const match = DATE_ONLY.exec(value);
    if (match) {
      // A date without a time (a target date) is that calendar day, never shifted.
      return new TZDate(Number(match[1]), Number(match[2]) - 1, Number(match[3]), TIME_ZONE);
    }
    return new TZDate(new Date(value), TIME_ZONE);
  }
  return new TZDate(value, TIME_ZONE);
}

/** `Nov 11, 2026` */
export function formatDate(value: DateInput): string {
  return format(manila(value), "MMM d, yyyy");
}

/** `Nov 11, 2026, 3:45 PM` */
export function formatDateTime(value: DateInput): string {
  return format(manila(value), "MMM d, yyyy, h:mm a");
}

/** `Nov 11`, with the year only when it is not the current year. */
export function formatShortDate(value: DateInput, now: Date = new Date()): string {
  const date = manila(value);
  const sameYear = date.getFullYear() === manila(now).getFullYear();
  return format(date, sameYear ? "MMM d" : "MMM d, yyyy");
}

/** `Wednesday, Nov 11, 2026` */
export function formatLongDate(value: DateInput): string {
  return format(manila(value), "EEEE, MMM d, yyyy");
}

/**
 * `2 days ago` within the last seven days, otherwise the date.
 * Show the exact time next to it (see the RelativeTime component).
 */
export function formatRelative(value: DateInput, now: Date = new Date()): string {
  const date = typeof value === "string" ? new Date(value) : value;
  const elapsed = now.getTime() - date.getTime();
  if (elapsed < 0 || elapsed > SEVEN_DAYS_MS) return formatDate(value);
  if (elapsed < 60_000) return "just now";
  return formatDistanceStrict(date, now, { addSuffix: true, roundingMethod: "floor" });
}

/** `₱125,000.00` */
export function formatMoney(amount: string | number): string {
  const value = typeof amount === "string" ? Number(amount) : amount;
  if (!Number.isFinite(value)) return "₱—";
  return `₱${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/** `84 KB`, `1.4 MB` */
export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** How long something has been waiting: `5 hours`, `3 days`. */
export function formatWaiting(hours: number): string {
  if (hours < 1) return "less than an hour";
  if (hours < 24) {
    const whole = Math.floor(hours);
    return `${whole} ${whole === 1 ? "hour" : "hours"}`;
  }
  const days = Math.floor(hours / 24);
  return `${days} ${days === 1 ? "day" : "days"}`;
}

/** Where a target date stands: `Due in 5 days`, `Due today`, `Overdue by 2 days`. */
export function describeDue(daysUntilTarget: number): string {
  if (daysUntilTarget === 0) return "Due today";
  if (daysUntilTarget === 1) return "Due tomorrow";
  if (daysUntilTarget > 1) return `Due in ${daysUntilTarget} days`;
  const late = Math.abs(daysUntilTarget);
  return `Overdue by ${late} ${late === 1 ? "day" : "days"}`;
}

/** Whole days between two moments, by the Manila calendar. */
export function calendarDaysBetween(later: DateInput, earlier: DateInput): number {
  return differenceInCalendarDays(manila(later), manila(earlier));
}

/** `Good morning`, `Good afternoon`, or `Good evening`, by Manila time. */
export function greeting(now: Date = new Date()): string {
  const hour = manila(now).getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

/** The number on a badge: "9+" above nine. */
export function badgeCount(count: number): string {
  return count > 9 ? "9+" : String(count);
}
