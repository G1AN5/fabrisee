import { describe, expect, it } from "vitest";

import { visibleNavItems } from "@/layouts/staffNav";
import { allPermissions, permissions } from "@/test/factories";

function labels(items: { label: string }[]): string[] {
  return items.map((item) => item.label);
}

describe("visibleNavItems (PR9: staff see only the functions of their role)", () => {
  it("shows every item to the administrator, with the admin pages marked", () => {
    const items = visibleNavItems(allPermissions());

    expect(labels(items)).toEqual([
      "Dashboard",
      "Projects",
      "Approvals",
      "Clients",
      "Notifications",
      "Users",
      "Settings",
      "Email outbox",
    ]);
    expect(labels(items.filter((item) => item.admin))).toEqual([
      "Users",
      "Settings",
      "Email outbox",
    ]);
  });

  it("hides the administration pages from a project manager", () => {
    const items = visibleNavItems(permissions("view_approvals", "view_clients", "manage_clients"));

    expect(labels(items)).toEqual([
      "Dashboard",
      "Projects",
      "Approvals",
      "Clients",
      "Notifications",
    ]);
  });

  it("hides the approvals page from production staff", () => {
    const items = visibleNavItems(permissions("view_clients"));

    expect(labels(items)).toEqual(["Dashboard", "Projects", "Clients", "Notifications"]);
  });

  it("keeps the pages that need no special permission", () => {
    expect(labels(visibleNavItems(permissions()))).toEqual([
      "Dashboard",
      "Projects",
      "Notifications",
    ]);
  });
});
