import { describe, expect, it } from "vitest";

import { destinationAfterSignIn } from "@/features/auth/redirects";
import type { CurrentUser } from "@/lib/types";
import { permissions } from "@/test/factories";

function user(home: CurrentUser["home_path"]): CurrentUser {
  return {
    id: 1,
    email: "pm@fabrisee.test",
    full_name: "Andrea Villanueva",
    short_name: "A. Villanueva",
    initials: "AV",
    role: home === "/app" ? "project_manager" : "client",
    role_label: home === "/app" ? "Project manager" : "Client",
    job_title: "",
    phone: "",
    client: home === "/app" ? null : { id: 1, company_name: "Aurelia Audio Labs" },
    is_company_staff: home === "/app",
    home_path: home,
    privacy_acknowledged_at: null,
    permissions: permissions(),
  };
}

describe("destinationAfterSignIn", () => {
  it("returns to the page the user came for", () => {
    expect(destinationAfterSignIn(user("/app"), "/app/projects/4/revisions")).toBe(
      "/app/projects/4/revisions",
    );
    expect(destinationAfterSignIn(user("/app"), "/app/projects?overdue=1")).toBe(
      "/app/projects?overdue=1",
    );
    expect(destinationAfterSignIn(user("/portal"), "/portal/projects/4/designs")).toBe(
      "/portal/projects/4/designs",
    );
  });

  it("goes to the user's own start page without a page to return to", () => {
    expect(destinationAfterSignIn(user("/app"), null)).toBe("/app");
    expect(destinationAfterSignIn(user("/portal"), "")).toBe("/portal");
  });

  it("never sends a client to the staff workspace or staff to the client portal", () => {
    expect(destinationAfterSignIn(user("/portal"), "/app/projects/4")).toBe("/portal");
    expect(destinationAfterSignIn(user("/app"), "/portal/projects/4")).toBe("/app");
  });

  it("ignores addresses outside FabriSee", () => {
    expect(destinationAfterSignIn(user("/app"), "https://example.test/app")).toBe("/app");
    expect(destinationAfterSignIn(user("/app"), "//example.test/app")).toBe("/app");
    expect(destinationAfterSignIn(user("/app"), "/application")).toBe("/app");
  });
});
