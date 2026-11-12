import path from "node:path";

import type { Locator, Page } from "@playwright/test";

import { ACCOUNTS, demoProjectIds, expect, signIn, test } from "./helpers";

/**
 * Captures the key screens with the demo data into docs/screenshots, at the two sizes of
 * the definition of done: 1440 × 900 (desktop) and 390 × 844 (phone). Run it with
 * `make screenshots` when a screen changes, and commit the pictures that changed.
 */

const SIZES = {
  desktop: { width: 1440, height: 900 },
  mobile: { width: 390, height: 844 },
} as const;

type Size = keyof typeof SIZES;

interface Shot {
  /** The file is named `<size>-<name>.png`. */
  name: string;
  /** A path, or a demo project by its number with the tab after it. */
  path: string | { project: string; tab?: string };
  /** Something that is on the screen once it is ready. */
  ready: (page: Page) => Locator;
  /** A part below the first screen to bring into view before the picture is taken. */
  focus?: (page: Page) => Locator;
  sizes: Size[];
}

interface Group {
  label: string;
  account: string | null;
  shots: Shot[];
}

const BOTH: Size[] = ["desktop", "mobile"];
const DESKTOP: Size[] = ["desktop"];

const heading = (name: string | RegExp) => (page: Page) => page.getByRole("heading", { name });

const GROUPS: Group[] = [
  {
    label: "sign-in page",
    account: null,
    shots: [{ name: "sign-in", path: "/login", ready: heading("Sign in"), sizes: BOTH }],
  },
  {
    label: "staff workspace as the project manager",
    account: ACCOUNTS.manager,
    shots: [
      {
        name: "dashboard-manager",
        path: "/app",
        ready: heading("Projects by stage"),
        sizes: BOTH,
      },
      {
        name: "projects-list",
        path: "/app/projects",
        ready: (page) => page.getByText("Showing 1 to 8 of 8 projects"),
        sizes: BOTH,
      },
      {
        name: "project-overview",
        path: { project: "FS-2026-0004" },
        ready: heading("Project details"),
        sizes: BOTH,
      },
      {
        name: "project-design-revisions",
        path: { project: "FS-2026-0004", tab: "revisions" },
        ready: (page) => page.getByRole("region", { name: "Approvals" }),
        focus: heading("Design R2"),
        sizes: BOTH,
      },
      {
        name: "project-quotations",
        path: { project: "FS-2026-0006", tab: "quotations" },
        ready: heading("Quotation v2"),
        sizes: DESKTOP,
      },
      {
        name: "project-progress",
        path: { project: "FS-2026-0002", tab: "progress" },
        ready: (page) => page.getByText("Moved from Design to Production"),
        sizes: DESKTOP,
      },
      {
        name: "project-documents",
        path: { project: "FS-2026-0001", tab: "documents" },
        ready: heading("Turnover documents"),
        sizes: DESKTOP,
      },
      {
        name: "notifications",
        path: "/app/notifications",
        ready: (page) => page.getByText(/Showing 1 to \d+ of \d+ notifications/),
        sizes: DESKTOP,
      },
    ],
  },
  {
    label: "dashboard of the designer",
    account: ACCOUNTS.designer,
    shots: [
      {
        name: "dashboard-designer",
        path: "/app",
        ready: heading(/Revisions to prepare/),
        sizes: DESKTOP,
      },
    ],
  },
  {
    label: "dashboard of production staff",
    account: ACCOUNTS.production,
    shots: [
      {
        name: "dashboard-production",
        path: "/app",
        ready: heading(/Approved and ready to build/),
        sizes: DESKTOP,
      },
    ],
  },
  {
    label: "client portal as a designated approver",
    account: ACCOUNTS.mark,
    shots: [
      { name: "portal-home", path: "/portal", ready: heading("Action needed"), sizes: BOTH },
      {
        name: "portal-project",
        path: { project: "FS-2026-0004" },
        ready: heading("Project details"),
        sizes: BOTH,
      },
      {
        name: "portal-designs",
        path: { project: "FS-2026-0004", tab: "designs" },
        ready: (page) => page.getByRole("region", { name: "Approvals" }),
        focus: heading("Design R2"),
        sizes: BOTH,
      },
    ],
  },
  {
    label: "client portal with a quotation to decide",
    account: ACCOUNTS.liza,
    shots: [
      {
        name: "portal-quotation",
        path: { project: "FS-2026-0007", tab: "quotation" },
        ready: heading("Quotation v1"),
        focus: heading("Quotation v1"),
        sizes: BOTH,
      },
    ],
  },
];

/** Waits until fonts, images, and data have arrived and the page has settled. */
async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(
      Array.from(document.images)
        .filter((image) => !image.complete)
        .map(
          (image) =>
            new Promise((resolve) => {
              image.addEventListener("load", resolve, { once: true });
              image.addEventListener("error", resolve, { once: true });
            }),
        ),
    );
  });
}

for (const size of Object.keys(SIZES) as Size[]) {
  test.describe(`screenshots at ${SIZES[size].width} × ${SIZES[size].height}`, () => {
    test.use({ viewport: SIZES[size], deviceScaleFactor: 2 });

    for (const group of GROUPS) {
      const shots = group.shots.filter((shot) => shot.sizes.includes(size));
      if (shots.length === 0) continue;

      test(group.label, async ({ page, request }, testInfo) => {
        testInfo.setTimeout(120_000);
        const directory = path.resolve(path.dirname(testInfo.file), "../../docs/screenshots");
        const ids = await demoProjectIds(request);
        const area = group.account?.endsWith("@fabrisee.test") ? "/app" : "/portal";
        if (group.account) await signIn(page, group.account);

        for (const shot of shots) {
          let target: string;
          if (typeof shot.path === "string") {
            target = shot.path;
          } else {
            const id = ids[shot.path.project];
            expect(id, `demo project ${shot.path.project}`).toBeDefined();
            target = `${area}/projects/${id}${shot.path.tab ? `/${shot.path.tab}` : ""}`;
          }

          await page.goto(target);
          await expect(shot.ready(page).first()).toBeVisible();
          await settle(page);
          if (shot.focus) {
            await shot
              .focus(page)
              .first()
              .evaluate((element) => element.scrollIntoView({ block: "start" }));
            // The page has a sticky top bar: leave room for it above the part of interest.
            await page.evaluate(() => window.scrollBy(0, -88));
            await settle(page);
          }

          await page.screenshot({
            path: path.join(directory, `${size}-${shot.name}.png`),
            animations: "disabled",
            caret: "hide",
          });
        }
      });
    }
  });
}
