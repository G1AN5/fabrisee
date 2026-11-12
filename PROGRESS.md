# FabriSee progress

## Status

Current milestone: **M2 done, in review** ([pull request 1](https://github.com/G1AN5/fabrisee/pull/1)) ·
Next: M3 (Session 2) · Last updated: 2026-11-12

## Done

### M0 — Foundation and developer experience

- Repository layout of the guide (section 3); Django 5.2 project with split settings (`dev`, `test`,
  `prod`), custom user model, DRF, SQLite with WAL, `dj-database-url`, WhiteNoise, drf-spectacular
  (development only).
- React 19 + TypeScript + Vite app with Tailwind CSS 4, shadcn/ui primitives, Inter (self-hosted),
  design tokens, React Router, TanStack Query; the Vite dev server proxies `/api` to Django.
- `Makefile`, `Procfile.dev`, `.env.example`, `.gitignore`, `.editorconfig`, dev container for
  Codespaces (installs, migrates, seeds, and starts the app by itself), CI workflow (backend,
  frontend, end to end), README, health endpoint `GET /api/health/`.

### M1 — Data model, authentication, roles, demo data

- All models of guide section 5 with migrations, database constraints (section 5.6), and admin pages
  with read-only history. `SystemSetting` (one row). Project numbers `FS-YYYY-NNNN`.
- Session sign-in with CSRF: `/api/auth/csrf/`, `login/`, `logout/`, `me/`, `session/`,
  `privacy-notice/`, `privacy-ack/`. Sign-in is rate limited.
- Roles and permissions: one capability map per role (`apps/accounts/permissions.py`) is the single
  source for the DRF permission classes and for the `permissions` the frontend receives. Querysets are
  scoped by role (PR9): a client user gets "not found" for anything of another client.
- `notify()` writes a `Notification` and an `EmailLog` entry (email is delivered when the database
  transaction commits). `ActivityLog` is append-only.
- `make seed` / `make reset-demo`: 4 fictitious clients, 10 users (all five roles), 8 projects that
  cover every stage and situation of guide section 12, with generated render images and PDF
  quotations, spec sheets, and turnover documents. Dates are relative to the day of seeding.

### M2 — App shell, design system, read-only views

- Read-only API: projects (list with filters, search, ordering; detail; timeline; quotations;
  revisions; documents), dashboard, pending approvals, clients, notifications (list, read, read all),
  and permission-checked file download with thumbnails.
- Shared components of guide section 11.5 (all of them; `FileDropzone` and `ConfirmDialog` are built
  and tested, and get their first screens in M3).
- Sign-in page (with the demo accounts while demo data is enabled), privacy notice dialog, staff
  workspace layout (sidebar, top bar, search with Ctrl+K, notification bell), client portal layout
  (top bar, bottom navigation on phones).
- Staff workspace: dashboard with role variants (designer: "Revisions to prepare"; production:
  "Approved and ready to build"), projects list (table from 1280 px, cards below), project page with
  header, stage tracker, next step, approved design card, and six tabs (Overview, Quotations, Design
  revisions, Progress, Documents, Activity), approvals page, notifications page.
- Client portal: My projects with "Action needed" first, project page with five tabs (Summary,
  Quotation, Designs, Progress, Documents), notifications page.
- "No access" (403) and "not found" (404) pages; loading skeletons, empty states, and error states
  with "Try again" on every screen.
- Pages of later milestones (New request, Clients, Users, Settings, Email outbox) show a short
  "not built yet" page that names their milestone.

### How it was checked (definition of done)

| Check | Result |
|---|---|
| `make test` | Passes: ruff, migrations in sync, 276 pytest tests; ESLint, Prettier, TypeScript, 69 Vitest tests |
| `make e2e` | Passes: 30 Playwright tests (sign-in for each role, PR9 visibility, the M2 screens). Each test also fails on an error or a warning in the browser console |
| CI on the pull request | Backend, Frontend, and End to end (Playwright) are green |
| `make dev` | Django on 8000, Vite on 5173, and the scheduler start together; no errors in the server log |
| Sizes | Every M2 screen checked at 1440 × 900 and 390 × 844 for each role; no sideways scrolling at 390 px |
| Screenshots | 24 pictures in [`docs/screenshots/`](docs/screenshots/) (`make screenshots`) |

Thesis test cases that already exist (the others arrive with their milestones):
`test_tc7_client_cannot_open_other_clients_project`, `test_tc8_production_sees_approved_revision_first`,
`test_tc9_dashboard_shows_stage_counts_pending_and_overdue`.

Process rules so far: **PR9** is enforced on every read path (API, files, pages) and tested. The
database already refuses a second sent quotation, a second pending revision, a change to an accepted
quotation, and a change to an approved revision. PR1 to PR8 get their services in M3 to M7; until
then the app is read-only on purpose.

## Next

**Session 2 (M3 to M5)**: project requests with file uploads, designated approvers, documents;
quotations with versions and decisions; design revisions with approvals and locking. Process rules
PR1 to PR5 and PR9 in backend services with tests TC1 to TC5, TC7, TC8.

Notes for that session:

- Write the services in `apps/*/services.py` and move the demo data onto them. Today the seed
  (`apps/core/demo/scenario.py`) writes the history records itself with back-dated timestamps, because
  no services existed yet; the services should accept a `now` argument so the seed can keep its dates.
- `next_project_number()`, `notify()`, `log_activity()`, `validate_upload()`, and `make_thumbnail()`
  exist and are tested. `RuleViolation(code, message, fields)` is the error to raise.
- The screens to add replace the placeholders in `frontend/src/router.tsx` (`ComingSoon`). The client
  portal already shows a note where the "Accept", "Return with comments", "Approve", and "Request
  changes" buttons will be.
- The "Remind" button of the dashboard and the approvals page arrives with M7 (PR6).

## Decisions

- 2026-11-11 SQLite with WAL through the Django ORM; Django 5.2 LTS and DRF
  ([0001](docs/decisions/0001-sqlite-and-django.md)).
- 2026-11-11 TypeScript 6.0 (not 7), hand-written shadcn/ui primitives, no jsx-a11y lint plugin yet,
  Node 22.22 or newer ([0002](docs/decisions/0002-frontend-toolchain-versions.md)).
- 2026-11-12 One capability map per role is the source for API permissions and for what the pages
  show; querysets are scoped by role; a client user who asks for a record of another client gets
  **404**, so the API does not reveal that it exists
  ([0003](docs/decisions/0003-permissions-and-visibility.md)).
- 2026-11-12 "Next step", "needs action", pending decisions, and the dashboard numbers all come from
  one place (`apps/projects/selectors.py`); text and control sizes are tokens that the client portal
  raises to a 16 px base ([0004](docs/decisions/0004-next-step-and-text-sizes.md)).
- 2026-11-12 The CI end-to-end job installs the Playwright browser without system packages (the apt
  step timed out on the runner); it installs them only if the browser does not start.
- 2026-11-12 `.claude/settings.json` pre-approves the project's own commands for Claude Code sessions.
  Merging a pull request is not pre-approved: the group reviews and merges.
- 2026-11-12 The client portal uses the tab names of the guide (`quotation`, `designs`) in its
  addresses; the staff workspace uses `quotations`, `revisions`.
- 2026-11-12 The projects table shows the manager column from 1400 px; below 1280 px the list is shown
  as cards (two columns from 768 px), which also name the manager.

## Implementation details to reflect in the thesis

Fields and tables beyond the thesis ERD. Those marked *(guide)* are already listed as *(impl.)* in the
build guide, section 5; the others were added while building.

- **User**: `job_title`, `privacy_acknowledged_at` *(guide)*; `created_at`, `updated_at`.
- **Project**: `status`, `designer`, `design_reopened`, `requires_requote` *(guide)*.
- **ProjectSequence** (new table): the last project number used in each year, so numbers are unique
  even when two requests arrive at the same moment.
- **StageUpdate**: `source` *(guide)*. A first stage update is written when the project is created
  (empty `from_stage`, to `request`), so the timeline starts with "Request received".
- **Document**: `thumbnail` *(guide)*.
- **Quotation**: `decided_on_behalf`, `decision_channel`, `last_reminded_at` *(guide)*;
  `recorded_by` (the staff member who recorded a decision on behalf of the client).
- **DesignRevision**: `last_reminded_at` *(guide)*; `thumbnail` (small preview of the render).
- **Approval**: `decided_on_behalf`, `decision_channel` *(guide)*; `recorded_by`.
- **EmailLog**, **SystemSetting** *(guide)*.
- API additions beyond the guide: `GET /api/auth/session/` (answers "nobody is signed in" without an
  error, so the sign-in page has a clean console), `GET /api/demo/accounts/` (only while demo data is
  enabled in development), list filters `waiting_on=client`, `due_within=7`, `project_type`, and the
  notification filter `category`.
- A returned quotation keeps the status "Returned" until a new version exists, then it becomes
  "Superseded"; the comment of the client stays on it.

## Questions for the group

Defaults of the guide (Appendix A) that are in use until the company confirms them:

1. **Reminder threshold (PR6)**: is 48 hours right?
2. **Who decides on a quotation**: any one designated approver (the setting also allows "all").
3. **Who approves a design**: all designated approvers of the project.
4. **Manager of a new request**: the first active project manager, editable afterwards.
5. **Project number format**: `FS-YYYY-NNNN`, starting again at 0001 each year.
6. **Project types**: store interior, display stand, brand sign, event booth, other.
7. **Upload limit**: 20 MB per file; JPG, PNG, WebP, and PDF only.

Choices made in this session that the group should confirm:

8. **Production staff and unapproved designs**: production staff see approved revisions and the
   history, but not a revision that still waits for approval (so nothing is built from an unapproved
   design). They see no quotations (guide section 7). Is that what the company wants?
9. **Remarks on stage changes** are shown to the client on the Progress tab. Should staff be able to
   add remarks that only staff see?
10. **Clients and Users pages**: the guide lists them (section 10.2) but no milestone builds them. I
    suggest Clients in M3 (it is needed to submit a request on behalf of a client) and Users in M7
    (with the invitation flow). Until then both show a "not built yet" page, and the Django admin can
    add clients and users.
11. **Privacy notice wording** (`backend/apps/accounts/privacy.md`): written from guide section 16.
    The group or the adviser should review the text before real clients use the system.
12. **Demo quotation and spec sheet PDFs**: their layout, terms, and prices are invented for the
    demo. If the company has a real quotation format, the demo files can follow it (without real
    client names or prices).

## Known issues

- **PDF preview**: a quotation or spec sheet is shown inside the page only where the browser has a
  built-in PDF viewer (desktop Chrome, Edge, Firefox, Safari). On phones the file is offered with
  "Open" and "Download". A viewer that works everywhere (PDF.js) can be added in M4 if the group
  wants it.
- **Forgot password** shows who to contact; email-based password reset arrives with M7 (email
  templates).
- **Demo dates age**: the demo data is relative to the day it was loaded. After a few days, run
  `make reset-demo` to get the intended situations again ("sent 3 days ago").
- **Playwright browser in Claude Code cloud sessions**: the browser download is blocked there. Use
  the installed Chromium: `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/opt/pw-browsers/chromium make e2e`.
  Codespaces and CI download the browser normally.
- **Screenshots change with the date** (relative times such as "2 days ago"), so `make screenshots`
  always produces different files. Commit them only when a screen changed.
- The manager column of the projects table is hidden between 1280 px and 1400 px to keep the "Next
  step" sentence readable; the project page shows the manager at every size.
