import { describe, expect, it } from "vitest";

import { approvalSummary, onBehalfText } from "@/lib/approvals";
import { approvalLine, person } from "@/test/factories";

describe("approvalSummary", () => {
  it("counts the approvals until everybody approved", () => {
    expect(approvalSummary(0, 2)).toBe("0 of 2 approved");
    expect(approvalSummary(1, 2)).toBe("1 of 2 approved");
    expect(approvalSummary(2, 2)).toBe("Approved by all designated approvers");
    expect(approvalSummary(1, 1)).toBe("Approved by the designated approver");
  });

  it("says so when nobody is designated", () => {
    expect(approvalSummary(0, 0)).toBe("No designated approvers yet");
  });
});

describe("onBehalfText", () => {
  it("is empty for a decision the approver made in the portal", () => {
    expect(onBehalfText(approvalLine({ decision: "approved", state: "approved" }))).toBeNull();
  });

  it("names who recorded the decision, for whom, and through which channel", () => {
    const line = approvalLine({
      approver: person({ full_name: "Nico Ramos", short_name: "N. Ramos" }),
      decision: "approved",
      state: "approved",
      decided_on_behalf: true,
      decision_channel: "phone",
      decision_channel_label: "Phone",
      recorded_by: person({ full_name: "Andrea Villanueva", short_name: "A. Villanueva" }),
    });

    expect(onBehalfText(line)).toBe("Recorded by A. Villanueva on behalf of N. Ramos (phone)");
  });

  it("still reads well without a recorder or a channel", () => {
    const line = approvalLine({ decided_on_behalf: true });

    expect(onBehalfText(line)).toBe("Recorded by staff on behalf of M. Bautista");
  });
});
