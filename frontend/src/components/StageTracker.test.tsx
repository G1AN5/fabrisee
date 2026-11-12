import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StageChip } from "@/components/StageChip";
import { StageSteps, StageTracker } from "@/components/StageTracker";
import type { StageDates } from "@/lib/types";

const DATES: StageDates = {
  request: "2026-09-27T08:55:00+08:00",
  design: "2026-10-01T19:12:00+08:00",
  production: "2026-11-06T14:05:00+08:00",
  delivery_installation: null,
  turnover: null,
};

describe("StageTracker", () => {
  it("lists the five stages in order", () => {
    render(<StageTracker stage="production" stageDates={DATES} />);

    const steps = within(screen.getByRole("list", { name: "Project stages" })).getAllByRole(
      "listitem",
    );
    expect(steps.map((step) => step.textContent)).toEqual([
      expect.stringContaining("Request"),
      expect.stringContaining("Design"),
      expect.stringContaining("Production"),
      expect.stringContaining("Delivery and Installation"),
      expect.stringContaining("Turnover"),
    ]);
  });

  it("marks the current stage and says in words where each stage stands", () => {
    render(<StageTracker stage="production" stageDates={DATES} />);

    const steps = screen.getAllByRole("listitem");
    expect(steps[2]).toHaveAttribute("aria-current", "step");
    expect(steps.filter((step) => step.hasAttribute("aria-current"))).toHaveLength(1);
    expect(steps[0]).toHaveTextContent("Request (completed)");
    expect(steps[1]).toHaveTextContent("Design (completed)");
    expect(steps[2]).toHaveTextContent("Production (current stage)");
    expect(steps[3]).toHaveTextContent("Delivery and Installation (not started)");
    expect(steps[4]).toHaveTextContent("Turnover (not started)");
  });

  it("shows the date a stage was entered only for the stages reached", () => {
    render(<StageTracker stage="production" stageDates={{ ...DATES, turnover: DATES.request }} />);

    const steps = screen.getAllByRole("listitem");
    expect(steps[0]).toHaveTextContent("Sep 27");
    expect(steps[1]).toHaveTextContent("Oct 1");
    expect(steps[2]).toHaveTextContent("Nov 6");
    // A date on a stage that is still to come is not shown.
    expect(steps[4]).not.toHaveTextContent("Sep 27");
  });

  it("has no current stage once the project is completed", () => {
    render(<StageTracker stage="turnover" status="completed" />);

    const steps = screen.getAllByRole("listitem");
    expect(steps.some((step) => step.hasAttribute("aria-current"))).toBe(false);
    expect(steps[4]).toHaveTextContent("Turnover (completed)");
  });
});

describe("StageSteps and StageChip", () => {
  it("describe the stage in words for screen readers", () => {
    render(<StageSteps stage="delivery_installation" />);

    expect(
      screen.getByRole("img", { name: "Stage 4 of 5: Delivery and Installation" }),
    ).toBeInTheDocument();
  });

  it("always show the stage name, also in the short form", () => {
    const { rerender } = render(<StageChip stage="delivery_installation" />);
    expect(screen.getByText("Delivery and Installation")).toBeInTheDocument();

    rerender(<StageChip stage="delivery_installation" short />);
    expect(screen.getByText("Delivery")).toBeInTheDocument();
    // The full name stays available to screen readers.
    expect(screen.getByText("Delivery and Installation")).toHaveClass("sr-only");
  });
});
