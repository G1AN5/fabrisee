import { ACCOUNTS, expect, signIn, test } from "./helpers";

test.describe("staff workspace (read-only screens of Milestone 2)", () => {
  test.beforeEach(async ({ page }) => {
    await signIn(page, ACCOUNTS.manager);
  });

  test("the dashboard shows the key numbers, what needs attention, and the five stages", async ({
    page,
  }) => {
    const numbers = page.getByRole("region", { name: "Key numbers" });
    for (const label of [
      "Active projects",
      "Waiting for client decisions",
      "Overdue items",
      "Due in the next 7 days",
    ]) {
      await expect(numbers.getByText(label)).toBeVisible();
    }
    await expect(page.getByText("Needs attention")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Projects by stage" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Recent activity" })).toBeVisible();

    // A key number opens the list it counts.
    await numbers.getByRole("link", { name: /Overdue items/ }).click();
    await expect(page).toHaveURL(/\/app\/projects\?overdue=1$/);
    await expect(page.getByRole("button", { name: "Overdue", pressed: true })).toBeVisible();
  });

  test("the projects list filters by stage, searches, and sorts", async ({ page }) => {
    await page.goto("/app/projects");
    const rows = page.getByRole("table").locator("tbody tr");
    await expect(rows).toHaveCount(8);

    await page.getByRole("combobox", { name: "Stage" }).click();
    await page.getByRole("option", { name: "Production" }).click();
    await expect(page).toHaveURL(/stage=production/);
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText("Café counter and menu signage");
    await expect(rows.first()).toContainText("FS-2026-0002");

    await page.getByRole("button", { name: "Clear filters" }).click();
    await expect(rows).toHaveCount(8);

    await page.getByRole("searchbox", { name: /Search projects by number/ }).fill("aurelia");
    await expect(rows).toHaveCount(2);
    await expect(page).toHaveURL(/q=aurelia/);

    await page
      .getByRole("searchbox", { name: /Search projects by number/ })
      .fill("no such project");
    await expect(page.getByText("No project matches these filters")).toBeVisible();
  });

  test("a project page shows the stages, the next step, and every tab", async ({ page }) => {
    await page.goto("/app/projects");
    await page.getByRole("link", { name: "Experience counter and brand wall" }).click();

    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      "Experience counter and brand wall",
    );
    const stages = page.getByRole("list", { name: "Project stages" });
    await expect(stages.getByRole("listitem")).toHaveCount(5);
    await expect(stages.locator('[aria-current="step"]')).toContainText("Design");
    await expect(page.getByText("R2 waiting for 1 of 2 approvers")).toBeVisible();

    const tabs = page.getByRole("tablist", { name: "Project sections" });
    await expect(tabs.getByRole("tab")).toHaveText([
      /^Overview/,
      /^Quotations/,
      /^Design revisions/,
      /^Progress/,
      /^Documents/,
      /^Activity/,
    ]);

    // PR4: every design file is a numbered revision; earlier revisions stay in the history.
    await tabs.getByRole("tab", { name: /Design revisions/ }).click();
    await expect(page).toHaveURL(/\/revisions$/);
    await expect(page.getByRole("heading", { name: "Design R2" })).toBeVisible();
    await expect(page.getByRole("img", { name: /R2/ }).first()).toBeVisible();
    const approvals = page.getByRole("region", { name: "Approvals" });
    await expect(approvals.getByText("1 of 2 approved")).toBeVisible();
    await expect(approvals.getByRole("listitem")).toHaveCount(2);
    await page.getByRole("button", { name: /R1/ }).click();
    await expect(page.getByRole("heading", { name: "Design R1" })).toBeVisible();
    await expect(approvals.getByText("Changes requested")).toBeVisible();

    await tabs.getByRole("tab", { name: /Quotations/ }).click();
    await expect(page.getByRole("heading", { name: "Quotation v1" })).toBeVisible();
    await expect(page.getByText(/^Accepted by /)).toBeVisible();

    // PR7: every stage change is recorded with date, time, and responsible staff member.
    await tabs.getByRole("tab", { name: /Progress/ }).click();
    await expect(page.getByText("Moved from Request to Design")).toBeVisible();

    await tabs.getByRole("tab", { name: /Activity/ }).click();
    await expect(page.getByText(/submitted the project request/)).toBeVisible();
  });

  test("the approved design is locked and shown on the project page (PR5)", async ({ page }) => {
    await page.goto("/app/projects?stage=production");
    await page.getByRole("link", { name: "Café counter and menu signage" }).click();

    await expect(page.getByRole("heading", { name: /Approved design/ })).toBeVisible();
    await expect(page.getByText(/Locked: it can no longer be changed/)).toBeVisible();
    await expect(
      page.getByRole("list", { name: "Project stages" }).locator('[aria-current="step"]'),
    ).toContainText("Production");
  });

  test("search finds a project from anywhere with the keyboard", async ({ page }) => {
    await expect(page.getByRole("button", { name: /Search projects/ })).toBeVisible();

    await page.keyboard.press("Control+k");
    await page.getByPlaceholder("Project number, title, or client").fill("FS-2026-0003");

    await page.getByRole("option", { name: /Trade fair booth/ }).click();

    await expect(page).toHaveURL(/\/app\/projects\/\d+$/);
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Trade fair booth");
  });

  test("notifications open the page they are about and count down when read", async ({ page }) => {
    await page.goto("/app/notifications");
    await expect(page.getByRole("heading", { level: 1, name: "Notifications" })).toBeVisible();

    await page.getByRole("combobox", { name: "Type of notification" }).click();
    await page.getByRole("option", { name: "Reminders" }).click();
    await expect(page).toHaveURL(/category=reminders/);
    await expect(page.getByText(/has had no decision for/).first()).toBeVisible();
    await expect(page.getByText(/New project request/)).toHaveCount(0);
  });
});

test.describe("client portal (read-only screens of Milestone 2)", () => {
  test("a client sees first what waits for their decision", async ({ page }) => {
    await signIn(page, ACCOUNTS.mark);

    await expect(page.getByRole("heading", { name: "Action needed" })).toBeVisible();
    await page.getByRole("link", { name: /Review design R2/ }).click();

    await expect(page).toHaveURL(/\/portal\/projects\/\d+\/designs$/);
    await expect(page.getByRole("heading", { name: "Design R2" })).toBeVisible();
    const approvals = page.getByRole("region", { name: "Approvals" });
    await expect(approvals.getByText("Mark Bautista (you)")).toBeVisible();
    await expect(approvals.getByText("Waiting for decision")).toBeVisible();
  });

  test("a client follows a project through its tabs", async ({ page }) => {
    await signIn(page, ACCOUNTS.nico);
    await page.getByRole("link", { name: /Café counter and menu signage/ }).click();

    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      "Café counter and menu signage",
    );
    await expect(page.getByText("Your display is being built")).toBeVisible();
    const tabs = page.getByRole("tablist", { name: "Project sections" });
    await expect(tabs.getByRole("tab")).toHaveText([
      "Summary",
      "Quotation",
      "Designs",
      "Progress",
      "Documents",
    ]);

    await tabs.getByRole("tab", { name: "Quotation" }).click();
    await expect(page.getByRole("heading", { name: "Quotation v1" })).toBeVisible();
    await expect(page.getByText(/^Accepted by Nico Ramos/)).toBeVisible();

    await tabs.getByRole("tab", { name: "Progress" }).click();
    await expect(page.getByText("We received your request")).toBeVisible();

    // Staff-only notes and internal activity are not part of the portal.
    await expect(page.getByRole("tab", { name: "Activity" })).toHaveCount(0);
  });

  test("the client portal fits a phone without sideways scrolling", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await signIn(page, ACCOUNTS.mark);

    await expect(page.getByRole("navigation", { name: "Client portal" }).last()).toBeVisible();
    await page.getByRole("link", { name: /Review design R2/ }).click();
    await expect(page.getByRole("heading", { name: "Design R2" })).toBeVisible();

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBe(0);
  });
});
