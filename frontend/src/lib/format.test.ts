import { describe, expect, it } from "vitest";

import {
  describeDue,
  formatDate,
  formatDateTime,
  formatFileSize,
  formatLongDate,
  formatMoney,
  formatRelative,
  formatShortDate,
  formatWaiting,
  greeting,
} from "@/lib/format";

// 3:45 PM in Manila (UTC+8) on Nov 11, 2026.
const MOMENT = "2026-11-11T07:45:00Z";
const NOW = new Date("2026-11-11T08:00:00Z");

describe("dates", () => {
  it("formats dates and times in Manila time", () => {
    expect(formatDate(MOMENT)).toBe("Nov 11, 2026");
    expect(formatDateTime(MOMENT)).toBe("Nov 11, 2026, 3:45 PM");
    expect(formatLongDate(MOMENT)).toBe("Wednesday, Nov 11, 2026");
  });

  it("uses the Manila calendar day near midnight", () => {
    // 11:30 PM on Nov 10 in UTC is already 7:30 AM on Nov 11 in Manila.
    expect(formatDate("2026-11-10T23:30:00Z")).toBe("Nov 11, 2026");
    expect(formatDateTime("2026-11-10T23:30:00Z")).toBe("Nov 11, 2026, 7:30 AM");
  });

  it("keeps a date without time on its calendar day", () => {
    expect(formatDate("2026-11-20")).toBe("Nov 20, 2026");
    expect(formatDate("2027-01-01")).toBe("Jan 1, 2027");
  });

  it("leaves out the year of short dates in the current year", () => {
    expect(formatShortDate("2026-11-03", NOW)).toBe("Nov 3");
    expect(formatShortDate("2025-11-03", NOW)).toBe("Nov 3, 2025");
  });

  it("shows relative times within seven days and the date after that", () => {
    expect(formatRelative("2026-11-11T07:59:40Z", NOW)).toBe("just now");
    expect(formatRelative("2026-11-11T07:45:00Z", NOW)).toBe("15 minutes ago");
    expect(formatRelative("2026-11-11T05:00:00Z", NOW)).toBe("3 hours ago");
    expect(formatRelative("2026-11-08T20:00:00Z", NOW)).toBe("2 days ago");
    expect(formatRelative("2026-11-01T08:00:00Z", NOW)).toBe("Nov 1, 2026");
  });

  it("greets by the time of day in Manila", () => {
    expect(greeting(new Date("2026-11-11T01:00:00Z"))).toBe("Good morning");
    expect(greeting(new Date("2026-11-11T07:00:00Z"))).toBe("Good afternoon");
    expect(greeting(new Date("2026-11-11T12:00:00Z"))).toBe("Good evening");
  });
});

describe("money and sizes", () => {
  it("formats pesos with two decimals", () => {
    expect(formatMoney("125000.00")).toBe("₱125,000.00");
    expect(formatMoney(96500)).toBe("₱96,500.00");
    expect(formatMoney("1234567.5")).toBe("₱1,234,567.50");
  });

  it("formats file sizes", () => {
    expect(formatFileSize(512)).toBe("512 B");
    expect(formatFileSize(84_000)).toBe("82 KB");
    expect(formatFileSize(1_500_000)).toBe("1.4 MB");
    expect(formatFileSize(null)).toBe("");
  });
});

describe("waiting and due texts", () => {
  it("describes how long a decision has been waiting", () => {
    expect(formatWaiting(0.4)).toBe("less than an hour");
    expect(formatWaiting(1.2)).toBe("1 hour");
    expect(formatWaiting(20)).toBe("20 hours");
    expect(formatWaiting(85.5)).toBe("3 days");
  });

  it("describes where a target date stands", () => {
    expect(describeDue(5)).toBe("Due in 5 days");
    expect(describeDue(1)).toBe("Due tomorrow");
    expect(describeDue(0)).toBe("Due today");
    expect(describeDue(-1)).toBe("Overdue by 1 day");
    expect(describeDue(-2)).toBe("Overdue by 2 days");
  });
});
