# CLAUDE.md — FabriSee

Instructions for Claude Code. This file is loaded at the start of every session. Keep it short; the full
specification is in `FABRISEE_BUILD_GUIDE.md`, and the current state of the work is in `PROGRESS.md`.

## What FabriSee is

FabriSee is a web-based **client management system** for the commercial display projects of **Five Brothers
Solutions Inc.**, a custom fabrication company in Parañaque City (store interiors, product display stands, brand
signs, event booths). It is the system of a BS IT thesis (Mapúa University). It has two sides:

- **Client portal**: clients submit project requests, accept or return quotations, approve or request changes to
  design revisions, and follow the progress of their projects.
- **Staff workspace**: staff keep client and project records, upload quotations and numbered design revisions,
  record project stages, keep project documents, and see a management dashboard.

Every quotation, revision, approval, and stage change is recorded with its date, time, and user, and FabriSee
sends email and in-app notifications and reminders for decisions left pending.

## Read first, every session

1. `PROGRESS.md` — what is done, what is next, open questions. Create it in Milestone 0 if it does not exist.
2. `FABRISEE_BUILD_GUIDE.md` — the specification: stack, data model, process rules, screens, design system,
   milestones with acceptance criteria. When this file and the guide disagree, the guide wins; record the
   conflict in `PROGRESS.md`.

## Fixed decisions (do not change without writing down why in `docs/decisions/`)

- Backend: **Python 3.12, Django 5.2 LTS, Django REST Framework**, service layer for all business rules.
- Database: **SQLite** through the Django ORM (file in `backend/data/`, never committed). No external database
  service. PostgreSQL must keep working by setting `DATABASE_URL` (use `dj-database-url`), so avoid
  SQLite-only SQL.
- Frontend: **React + TypeScript + Vite**, **Tailwind CSS + shadcn/ui** (Radix), **TanStack Query**,
  **React Router**, **React Hook Form + Zod**, **lucide-react** icons, Inter font self-hosted with Fontsource.
- Auth: Django **session authentication** with CSRF, same origin (Vite dev server proxies `/api` to Django; in
  production Django serves the built frontend). No JWT.
- Files: Django `FileField` on local disk under `backend/media/` (never committed), served **only** through
  permission-checked API views. Images and PDF only.
- Email: a database-backed email log in development (viewable on an admin "Email outbox" page) plus console
  output; SMTP from environment variables in production.
- Scheduled reminders: a management command (`run_scheduler`) that calls the reminder service every few minutes;
  cron can call `send_due_reminders` in production.

## Commands (create these in Milestone 0 and keep them working)

- `make setup` — install backend and frontend dependencies, migrate, seed demo data.
- `make dev` — run Django (port 8000), Vite (port 5173), and the scheduler together (honcho + `Procfile.dev`).
- `make test` — ruff, pytest, ESLint, TypeScript check, Vitest.
- `make e2e` — Playwright tests (optional where browsers cannot be installed).
- `make seed` / `make reset-demo` — load or reset the demo data.
- Open the app at `http://localhost:5173` (in Codespaces, the forwarded port 5173).

## Process rules — implement in backend services, enforce on every path, test each one

- **PR1** A request cannot be submitted unless project type, location, target date, and dimensions are filled in.
- **PR2** Each submitted request becomes a project with a unique project number and the stage **Request**.
- **PR3** Accepting a quotation moves the project to **Design**; returning it with comments requires a new
  quotation version.
- **PR4** Every design file is a numbered revision (R1, R2, …); earlier revisions stay in the history.
- **PR5** When **all** designated approvers approve a revision, it is **locked** as the approved design and the
  project moves to **Production**; if any approver requests changes, comments are saved and a new revision is
  required.
- **PR6** A quotation or revision without a decision after the reminder threshold (default 48 hours, setting)
  triggers a reminder to the pending approvers and an alert to the project manager.
- **PR7** Every stage change (Production → Delivery and Installation → Turnover) is recorded with date, time, and
  responsible staff member, and the client is notified.
- **PR8** A change requested after approval needs a new approved revision (and an accepted revised quotation if the
  cost changes) before production continues.
- **PR9** Clients see only their own projects; staff see only the functions allowed for their role.

Stages, in order: **Request → Design → Production → Delivery and Installation → Turnover**. Stage changes into
Design and Production happen only through PR3 and PR5; an admin override exists only with a mandatory reason.

## Roles

`client`, `admin` (owner), `project_manager`, `designer`, `production`. The permission matrix is in the guide
(section 7). Check permissions in the API (DRF permission classes and queryset scoping), not only in the UI.

## Conventions

- Backend: apps under `backend/apps/`; business logic in `services.py` (wrapped in `transaction.atomic`), thin
  views and serializers; every service writes an `ActivityLog` entry and triggers notifications through
  `apps.notifications.services.notify(...)`. Ruff for lint and format. Time zone `Asia/Manila`, `USE_TZ = True`.
- Tests: pytest + pytest-django + factory_boy. Name the tests for the thesis test cases `test_tc1_...` to
  `test_tc10_...` (guide section 13). Every process rule has at least one passing and one failing-path test.
- Frontend: feature folders under `src/features/`; shared UI in `src/components/`; shadcn primitives in
  `src/components/ui/`; API calls only through `src/lib/api.ts` and TanStack Query hooks; strict TypeScript;
  no `any` without a comment explaining why.
- Use the thesis terms in the UI and code: client portal, staff workspace, quotation, design revision, designated
  approver, approved design, project stage, management dashboard, project document repository.

## Design system essentials (full spec in guide section 11)

- Calm, precise, crafted: "blueprint and workshop". Light theme first; tokens as CSS variables.
- Primary (blueprint blue) `#1E40AF`, hover `#1E3A8A`; text `#0F172A`; muted text `#64748B`; page `#F8FAFC`;
  cards white with `#E2E8F0` borders; input borders `#8291A5`; focus ring `#2563EB`; workshop orange `#C2410C`
  for brand accents only (never for status).
- Stage chips: Request slate, Design indigo, Production orange, Delivery and Installation cyan, Turnover green —
  always text + color, never color alone.
- Inter, 14 px base in the staff workspace, 16 px in the client portal; generous whitespace; 8 px radius on
  controls, 12 px on cards; subtle shadows; skeletons for loading; helpful empty states.
- Mobile-first client portal (clients approve on phones); desktop-first staff workspace that still works at
  390 px width. WCAG 2.1 AA contrast and full keyboard access.

## Definition of done (every milestone)

- `make test` passes; the app starts with `make dev`; no errors in the browser console or the server log.
- New screens checked at 1440 × 900 and 390 × 844 (Playwright screenshots in `docs/screenshots/` when browsers
  can be installed; otherwise describe what was checked).
- `PROGRESS.md` updated (done, next, decisions, questions for the group). README updated if commands changed.
- Small, descriptive commits. At the end of the session, open a pull request (or push the branch and say so) that
  summarizes the milestone, lists how to try it, and lists questions for the group.

## Do not

- Do not add 3D or AR viewers, CNC or machine integration, kiosk features, online payments, SMS, native mobile apps,
  AI chatbots, cost computation, inventory, payroll, or accounting. They are outside the thesis scope.
- Do not use real client brand names or real personal data in seed data, tests, or screenshots. Use the
  fictitious clients defined in the guide.
- Do not commit secrets, `.env` files, the SQLite database, media uploads, `node_modules`, or virtual environments.
- Do not add a third-party database or backend-as-a-service (Supabase, Firebase, etc.).
- Do not weaken a process rule to make a test or a screen easier.

## Environment notes

- Codespaces: Vite must listen on `0.0.0.0`, allow hosts ending in `.app.github.dev`, and use HMR client port 443
  when the `CODESPACES` variable is set; Django needs `.app.github.dev` in `ALLOWED_HOSTS` and
  `https://*.app.github.dev` in `CSRF_TRUSTED_ORIGINS` (development settings only).
- Claude Code cloud sessions can install packages from the common registries. If Playwright browsers cannot be
  downloaded, skip `make e2e` locally, note it in `PROGRESS.md`, and rely on the GitHub Actions workflow.
