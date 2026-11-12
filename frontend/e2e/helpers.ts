import { type APIRequestContext, test as base, expect, type Page } from "@playwright/test";

/** The demo accounts of `make seed` (build guide, Appendix B). Never use them in production. */
export const DEMO_PASSWORD = "FabriSee@2026";

export const ACCOUNTS = {
  owner: "owner@fabrisee.test",
  manager: "pm@fabrisee.test",
  designer: "designer@fabrisee.test",
  production: "production@fabrisee.test",
  /** Aurelia Audio Labs: one of two designated approvers. */
  mark: "mark@aurelia.test",
  /** Tindahan Tech PH: decides on quotation v1 of FS-2026-0007. */
  liza: "liza@tindahantech.test",
  /** Kapetirya Coffee House. */
  nico: "nico@kapetirya.test",
  /** Lunaria Skin Studio: has not acknowledged the privacy notice yet. */
  ella: "ella@lunaria.test",
} as const;

interface Fixtures {
  /**
   * Requests that are expected to fail in a test (a wrong password, a page of another
   * client): the browser reports them in the console, and that is not a defect.
   */
  allowFailedRequests: boolean;
  consoleProblems: string[];
}

/**
 * `test` that also fails when the browser console shows an error (definition of done:
 * "no errors in the browser console").
 */
export const test = base.extend<Fixtures>({
  allowFailedRequests: [false, { option: true }],
  consoleProblems: [
    async ({ page, allowFailedRequests }, use) => {
      const problems: string[] = [];
      page.on("console", (message) => {
        if (message.type() !== "error") return;
        if (allowFailedRequests && message.text().startsWith("Failed to load resource")) return;
        problems.push(message.text());
      });
      page.on("pageerror", (error) => problems.push(error.message));
      await use(problems);
      expect(problems, "errors in the browser console").toEqual([]);
    },
    { auto: true },
  ],
});

export { expect };

/** Fills in the sign-in form and submits it. */
export async function submitSignIn(page: Page, email: string, password = DEMO_PASSWORD) {
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
}

/** Signs in through the sign-in page and waits for the user's own area. */
export async function signIn(page: Page, email: string) {
  await page.goto("/login");
  await submitSignIn(page, email);
  await page.waitForURL(/\/(app|portal)(\/|\?|$)/);
}

/** Signs in through the API (for looking things up without a browser page). */
export async function apiSignIn(request: APIRequestContext, email: string) {
  await request.get("/api/auth/csrf/");
  const { cookies } = await request.storageState();
  const token = cookies.find((cookie) => cookie.name === "csrftoken")?.value ?? "";
  const response = await request.post("/api/auth/login/", {
    data: { email, password: DEMO_PASSWORD },
    headers: { "X-CSRFToken": token },
  });
  expect(response.ok(), `sign in as ${email}`).toBeTruthy();
}

/** The ids of the demo projects by project number (ids differ between databases). */
export async function demoProjectIds(request: APIRequestContext): Promise<Record<string, number>> {
  await apiSignIn(request, ACCOUNTS.manager);
  const response = await request.get("/api/projects/?page_size=100");
  expect(response.ok()).toBeTruthy();
  const body = (await response.json()) as { results: { id: number; project_number: string }[] };
  return Object.fromEntries(body.results.map((project) => [project.project_number, project.id]));
}
