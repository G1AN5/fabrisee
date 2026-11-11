import { expect, test } from "@playwright/test";

test("the API answers through the Vite proxy", async ({ request }) => {
  const response = await request.get("/api/health/");

  expect(response.ok()).toBeTruthy();
  expect(await response.json()).toMatchObject({ status: "ok", database: "ok" });
});

test("the app loads without browser console errors", async ({ page }) => {
  const problems: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") problems.push(message.text());
  });
  page.on("pageerror", (error) => problems.push(error.message));

  await page.goto("/");

  await expect(page.getByRole("img", { name: "FabriSee" }).first()).toBeVisible();
  expect(problems).toEqual([]);
});
