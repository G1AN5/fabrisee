import { ACCOUNTS, demoProjectIds, expect, signIn, test } from "./helpers";

/**
 * Process rule PR9: clients see only their own projects, and staff see only the
 * functions allowed for their role. The API enforces it; the pages follow.
 */
test.describe("PR9: visibility", () => {
  // Opening something that is not yours answers 403 or 404, which the browser logs.
  test.use({ allowFailedRequests: true });

  test("a client sees only the projects of their own company", async ({ page }) => {
    await signIn(page, ACCOUNTS.mark);

    await expect(
      page.getByRole("link", { name: /Experience counter and brand wall/ }).first(),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: /Window display refresh/ })).toBeVisible();
    await expect(page.getByText("Café counter and menu signage")).toHaveCount(0);

    const list = (await (await page.request.get("/api/projects/")).json()) as {
      count: number;
      results: { client: { company_name: string } }[];
    };
    expect(list.count).toBe(2);
    expect(new Set(list.results.map((project) => project.client.company_name))).toEqual(
      new Set(["Aurelia Audio Labs"]),
    );
  });

  test("a client cannot open a project of another client", async ({ page, request }) => {
    const ids = await demoProjectIds(request);
    const other = ids["FS-2026-0002"]; // Kapetirya Coffee House
    await signIn(page, ACCOUNTS.mark);

    await page.goto(`/portal/projects/${other}`);

    await expect(page.getByText("We could not find this project")).toBeVisible();
    await expect(page.getByText("Café counter and menu signage")).toHaveCount(0);
    for (const path of ["", "quotations/", "revisions/", "documents/", "timeline/"]) {
      const response = await page.request.get(`/api/projects/${other}/${path}`);
      expect(response.status(), `/api/projects/${other}/${path}`).toBe(404);
    }
  });

  test("a client cannot use the staff workspace", async ({ page }) => {
    await signIn(page, ACCOUNTS.mark);

    await page.goto("/app");

    await expect(page.getByText("You do not have access to this page")).toBeVisible();
    for (const path of ["/api/dashboard/", "/api/approvals/pending/", "/api/clients/"]) {
      expect((await page.request.get(path)).status(), path).toBe(403);
    }
  });

  test("staff cannot use the client portal", async ({ page }) => {
    await signIn(page, ACCOUNTS.manager);

    await page.goto("/portal");

    await expect(page.getByText("You do not have access to this page")).toBeVisible();
  });

  test("production staff see no quotations and no approvals page", async ({ page, request }) => {
    const ids = await demoProjectIds(request);
    const project = ids["FS-2026-0002"];
    await signIn(page, ACCOUNTS.production);

    await page.goto(`/app/projects/${project}`);
    const tabs = page.getByRole("tablist", { name: "Project sections" });
    await expect(tabs.getByRole("tab", { name: /Design revisions/ })).toBeVisible();
    await expect(tabs.getByRole("tab", { name: /Quotations/ })).toHaveCount(0);
    expect((await page.request.get(`/api/projects/${project}/quotations/`)).status()).toBe(403);

    await page.goto("/app/approvals");
    await expect(page.getByText("You do not have access to this page")).toBeVisible();
  });

  test("only the administrator opens the administration pages", async ({ page }) => {
    await signIn(page, ACCOUNTS.manager);

    await page.goto("/app/settings");

    await expect(page.getByText("You do not have access to this page")).toBeVisible();
  });

  test("files are served only to signed-in users who may see the project", async ({
    page,
    request,
    playwright,
  }) => {
    const ids = await demoProjectIds(request);
    const project = ids["FS-2026-0002"]; // Kapetirya Coffee House
    const revisions = (await (await request.get(`/api/projects/${project}/revisions/`)).json()) as {
      render: { url: string };
    }[];
    const fileUrl = revisions[0]!.render.url;

    // The project manager gets the file.
    const allowed = await request.get(fileUrl);
    expect(allowed.status()).toBe(200);
    expect(allowed.headers()["content-type"]).toMatch(/^image\//);

    // A visitor who is not signed in does not.
    const anonymous = await playwright.request.newContext({ baseURL: "http://127.0.0.1:5173" });
    expect([401, 403]).toContain((await anonymous.get(fileUrl)).status());
    await anonymous.dispose();

    // A client of another company gets "not found", as for the project itself.
    await signIn(page, ACCOUNTS.mark);
    expect((await page.request.get(fileUrl)).status()).toBe(404);
  });
});
