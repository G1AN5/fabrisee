import { describe, expect, it } from "vitest";

import { decisionHref, pendingApproversText } from "@/features/dashboard/decisions";
import { pendingDecision, person } from "@/test/factories";

describe("decisionHref", () => {
  it("opens the tab of the item that waits for a decision", () => {
    expect(decisionHref(pendingDecision({ kind: "revision" }))).toBe("/app/projects/4/revisions");
    expect(decisionHref(pendingDecision({ kind: "quotation" }))).toBe("/app/projects/4/quotations");
  });

  it("opens the project when the viewer may not see the item itself", () => {
    expect(decisionHref(pendingDecision({ id: null }))).toBe("/app/projects/4");
  });
});

describe("pendingApproversText", () => {
  const joanna = person({ id: 2, full_name: "Joanna Cruz" });
  const mark = person({ id: 3, full_name: "Mark Bautista" });
  const liza = person({ id: 4, full_name: "Liza Mendoza" });

  it("names one or two approvers", () => {
    expect(pendingApproversText(pendingDecision({ pending_approvers: [mark] }))).toBe(
      "Waiting for Mark Bautista",
    );
    expect(pendingApproversText(pendingDecision({ pending_approvers: [joanna, mark] }))).toBe(
      "Waiting for Joanna Cruz and Mark Bautista",
    );
  });

  it("counts three or more approvers of a revision", () => {
    expect(pendingApproversText(pendingDecision({ pending_approvers: [joanna, mark, liza] }))).toBe(
      "Waiting for 3 approvers",
    );
  });

  it("says that any one approver can decide on a quotation", () => {
    const decision = pendingDecision({ kind: "quotation", pending_approvers: [joanna, mark] });

    expect(pendingApproversText(decision)).toBe("Waiting for one of 2 approvers");
  });

  it("points out a project without a designated approver", () => {
    expect(pendingApproversText(pendingDecision({ pending_approvers: [] }))).toBe(
      "No designated approver",
    );
  });
});
