import { describe, expect, it } from "vitest";

import { STAGES, stageIndex, stageInfo, stepState } from "@/lib/constants";

describe("stages", () => {
  it("are in the order of the thesis", () => {
    expect(STAGES.map((stage) => stage.label)).toEqual([
      "Request",
      "Design",
      "Production",
      "Delivery and Installation",
      "Turnover",
    ]);
    expect(stageIndex("request")).toBe(0);
    expect(stageIndex("turnover")).toBe(4);
  });

  it("each have a name, a short name, an icon, and chip colors", () => {
    for (const stage of STAGES) {
      const info = stageInfo(stage.value);
      expect(info.label).not.toBe("");
      expect(info.shortLabel).not.toBe("");
      expect(info.icon).toBeDefined();
      expect(info.chip).toContain("text-");
    }
  });
});

describe("stepState", () => {
  it("marks earlier stages as done and later ones as upcoming", () => {
    expect(stepState("request", "production")).toBe("done");
    expect(stepState("design", "production")).toBe("done");
    expect(stepState("production", "production")).toBe("current");
    expect(stepState("delivery_installation", "production")).toBe("upcoming");
    expect(stepState("turnover", "production")).toBe("upcoming");
  });

  it("treats the last stage of a completed project as done", () => {
    expect(stepState("turnover", "turnover", "active")).toBe("current");
    expect(stepState("turnover", "turnover", "completed")).toBe("done");
  });

  it("keeps the current stage for a project on hold or cancelled", () => {
    expect(stepState("design", "design", "on_hold")).toBe("current");
    expect(stepState("design", "design", "cancelled")).toBe("current");
  });
});
