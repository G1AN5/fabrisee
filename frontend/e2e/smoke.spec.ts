import { expect, test } from "./helpers";

test("the API answers through the Vite proxy", async ({ request }) => {
  const response = await request.get("/api/health/");

  expect(response.ok()).toBeTruthy();
  expect(await response.json()).toMatchObject({ status: "ok", database: "ok" });
});

test("a visitor sees the sign-in page, without browser console errors", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await expect(page.getByRole("img", { name: "FabriSee" }).first()).toBeVisible();
});
