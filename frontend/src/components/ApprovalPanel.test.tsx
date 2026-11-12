import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApprovalPanel } from "@/components/ApprovalPanel";
import { approvalLine, person } from "@/test/factories";

const joanna = person({ id: 2, full_name: "Joanna Cruz", short_name: "J. Cruz", initials: "JC" });
const mark = person({ id: 3, full_name: "Mark Bautista", short_name: "M. Bautista" });

describe("ApprovalPanel", () => {
  it("shows one line per designated approver with the decision and the comment", () => {
    render(
      <ApprovalPanel
        approvals={[
          approvalLine({
            approver: joanna,
            decision: "approved",
            state: "approved",
            comment: "Warm white is right.",
            decided_at: "2026-11-08T10:00:00+08:00",
          }),
          approvalLine({ approver: mark }),
        ]}
        approvedCount={1}
        approverCount={2}
      />,
    );

    const panel = screen.getByRole("region", { name: "Approvals" });
    const lines = within(panel).getAllByRole("listitem");
    expect(lines).toHaveLength(2);
    expect(within(panel).getByText("1 of 2 approved")).toBeInTheDocument();
    expect(lines[0]).toHaveTextContent("Joanna Cruz");
    expect(lines[0]).toHaveTextContent("Approved");
    expect(lines[0]).toHaveTextContent("Warm white is right.");
    expect(lines[1]).toHaveTextContent("Mark Bautista");
    expect(lines[1]).toHaveTextContent("Waiting for decision");
  });

  it("marks the line of the signed-in approver", () => {
    render(
      <ApprovalPanel
        approvals={[approvalLine({ approver: joanna }), approvalLine({ approver: mark })]}
        approvedCount={0}
        approverCount={2}
        currentUserId={mark.id}
      />,
    );

    const lines = screen.getAllByRole("listitem");
    expect(lines[0]).not.toHaveTextContent("(you)");
    expect(lines[1]).toHaveTextContent("Mark Bautista (you)");
  });

  it("labels a decision that staff recorded on behalf of the approver", () => {
    render(
      <ApprovalPanel
        approvals={[
          approvalLine({
            approver: mark,
            decision: "approved",
            state: "approved",
            decided_at: "2026-11-06T14:05:00+08:00",
            decided_on_behalf: true,
            decision_channel: "phone",
            decision_channel_label: "Phone",
            recorded_by: person({ id: 9, short_name: "A. Villanueva" }),
          }),
        ]}
        approvedCount={1}
        approverCount={1}
      />,
    );

    expect(
      screen.getByText(/Recorded by A\. Villanueva on behalf of M\. Bautista \(phone\)/),
    ).toBeInTheDocument();
    expect(screen.getByText("Approved by the designated approver")).toBeInTheDocument();
  });

  it("explains an empty panel", () => {
    render(<ApprovalPanel approvals={[]} approvedCount={0} approverCount={0} />);

    expect(screen.getByText("No designated approvers yet")).toBeInTheDocument();
    expect(
      screen.getByText("Nobody is designated to approve this project yet."),
    ).toBeInTheDocument();
  });
});
