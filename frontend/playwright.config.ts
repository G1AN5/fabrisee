import { defineConfig, devices } from "@playwright/test";

const isCI = Boolean(process.env.CI);

// Where Playwright's own browser cannot be downloaded (for example a Claude Code cloud
// session), point this at an installed Chromium instead.
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined;

/**
 * End-to-end tests run against the development servers with the demo data
 * (`make setup`, or `make reset-demo` for a clean state).
 *
 * - project `e2e`: the specs in e2e/ (`make e2e`)
 * - project `screenshots`: captures the key screens into docs/screenshots (`make screenshots`)
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  reporter: isCI ? [["list"], ["html", { open: "never" }]] : "list",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: isCI ? "on-first-retry" : "off",
    screenshot: "only-on-failure",
    launchOptions: { executablePath },
  },
  projects: [
    {
      name: "e2e",
      testIgnore: /screenshots\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "screenshots",
      testMatch: /screenshots\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "cd ../backend && .venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload",
      url: "http://127.0.0.1:8000/api/health/",
      reuseExistingServer: !isCI,
      timeout: 90_000,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !isCI,
      timeout: 90_000,
    },
  ],
});
