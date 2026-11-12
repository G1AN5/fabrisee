import { ACCOUNTS, expect, signIn, submitSignIn, test } from "./helpers";

const STAFF = [
  {
    role: "the owner (admin)",
    email: ACCOUNTS.owner,
    nav: [
      "Dashboard",
      "Projects",
      "Approvals",
      "Clients",
      "Notifications",
      "Users",
      "Settings",
      "Email outbox",
    ],
  },
  {
    role: "the project manager",
    email: ACCOUNTS.manager,
    nav: ["Dashboard", "Projects", "Approvals", "Clients", "Notifications"],
  },
  {
    role: "the designer",
    email: ACCOUNTS.designer,
    nav: ["Dashboard", "Projects", "Approvals", "Clients", "Notifications"],
  },
  {
    role: "production staff",
    email: ACCOUNTS.production,
    nav: ["Dashboard", "Projects", "Clients", "Notifications"],
  },
];

test.describe("sign-in by role", () => {
  for (const account of STAFF) {
    test(`${account.role} lands in the staff workspace with their own navigation`, async ({
      page,
    }) => {
      await signIn(page, account.email);

      await expect(page).toHaveURL(/\/app$/);
      await expect(page.getByRole("heading", { level: 1 })).toContainText(
        /^Good (morning|afternoon|evening),/,
      );
      const nav = page.getByRole("navigation", { name: "Staff workspace" });
      await expect(nav.getByRole("link")).toHaveText(
        account.nav.map((label) => new RegExp(`^${label}`)),
      );
    });
  }

  test("a client lands in the client portal", async ({ page }) => {
    await signIn(page, ACCOUNTS.mark);

    await expect(page).toHaveURL(/\/portal$/);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Hello, Mark");
    await expect(page.getByText("Projects of Aurelia Audio Labs")).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Staff workspace" })).toHaveCount(0);
  });

  test("the designer sees the revisions to prepare first", async ({ page }) => {
    await signIn(page, ACCOUNTS.designer);

    await expect(page.getByRole("heading", { name: /Revisions to prepare/ })).toBeVisible();
  });

  test("production staff see what is approved and ready to build first", async ({ page }) => {
    await signIn(page, ACCOUNTS.production);

    await expect(page.getByRole("heading", { name: /Approved and ready to build/ })).toBeVisible();
  });
});

test.describe("sign-in and sign-out", () => {
  test.use({ allowFailedRequests: true });

  test("a wrong password shows a message and keeps the visitor on the sign-in page", async ({
    page,
  }) => {
    await page.goto("/login");
    await submitSignIn(page, ACCOUNTS.manager, "not-the-password");

    await expect(page.getByRole("alert")).toContainText("The email or password is incorrect.");
    await expect(page).toHaveURL(/\/login$/);
    // The email stays in the form; nothing is lost.
    await expect(page.getByLabel("Email address")).toHaveValue(ACCOUNTS.manager);
  });

  test("an empty form names what is missing", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: "Sign in", exact: true }).click();

    await expect(page.getByText("Enter your email address.")).toBeVisible();
    await expect(page.getByText("Enter your password.")).toBeVisible();
  });

  test("a visitor is sent to the sign-in page and returns to the page they asked for", async ({
    page,
  }) => {
    await page.goto("/app/projects?overdue=1");

    await expect(page).toHaveURL(/\/login\?next=/);
    await submitSignIn(page, ACCOUNTS.manager);

    await expect(page).toHaveURL(/\/app\/projects\?overdue=1$/);
    await expect(page.getByRole("heading", { level: 1, name: "Projects" })).toBeVisible();
  });

  test("signing out ends the session", async ({ page }) => {
    await signIn(page, ACCOUNTS.manager);

    await page.getByRole("button", { name: /^Account menu of/ }).click();
    await page.getByRole("menuitem", { name: "Sign out" }).click();

    // The sign-in page starts fresh: it does not remember the page of the previous user.
    await expect(page).toHaveURL(/\/login$/);
    await page.goto("/app");
    await expect(page).toHaveURL(/\/login\?next=/);
    const session = await page.request.get("/api/auth/session/");
    expect(await session.json()).toEqual({ user: null });
  });

  test("a user who has not read the privacy notice sees it after signing in", async ({ page }) => {
    await signIn(page, ACCOUNTS.ella);
    const session = (await (await page.request.get("/api/auth/session/")).json()) as {
      user: { privacy_acknowledged_at: string | null };
    };
    test.skip(
      session.user.privacy_acknowledged_at !== null,
      "This account already acknowledged the notice in this database (run `make reset-demo`).",
    );

    const dialog = page.getByRole("dialog", { name: "Privacy notice" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("heading", { name: "What FabriSee keeps" })).toBeVisible();
    await expect(
      dialog.getByRole("button", { name: "I have read and understood this" }),
    ).toBeVisible();
  });
});
