# FabriSee Build Guide

Specification and plan for building **FabriSee: A Web-Based Client Management System for Commercial Display
Projects of a Custom Fabrication Company**. Written for Claude Code and for the thesis group (Delos Santos, Reyes,
Saluta). It turns Chapters 1–3 of the thesis into concrete decisions, screens, rules, and milestones.

Version 1 — 11 November 2026

---

## Contents

0. How to use this guide
1. Product brief
2. Architecture and stack
3. Repository layout
4. Development environment
5. Data model
6. Process rules as services
7. Roles and permissions
8. API
9. Notifications, email, and reminders
10. Screens and navigation
11. Visual design system
12. Demo data
13. Testing and quality
14. Milestones
15. Thesis alignment
16. Security and data privacy
17. Deployment (later)
18. Working agreement and session prompts
Appendix A. Values to confirm with the company

---

## 0. How to use this guide

**For Claude Code.** Read `CLAUDE.md`, this guide, and `PROGRESS.md` at the start of every session. Work through
the milestones in section 14 in order. Each milestone has tasks, acceptance criteria, and a demo script. Keep the
app runnable at the end of every session, update `PROGRESS.md`, and open one pull request per session (if you
cannot open it yourself, push the branch and say so, so the group can open it on GitHub). When a
decision depends on company facts that are not known, use the default in Appendix A, mark it in the code with
`# TO CONFIRM:` (or `// TO CONFIRM:`), and list it under "Questions for the group" in `PROGRESS.md` and the pull
request.

**For the group.** You do not need a local setup. Each Claude Code session works on its own branch and opens a
pull request. Review it on GitHub, merge it, and open the app in a GitHub Codespace (section 4.1) to try it.
Paste the next session prompt from section 18 to continue.

**Priorities, in order:** (1) the process rules work and are tested; (2) the main flows feel effortless for staff
and clients; (3) the interface looks polished and consistent; (4) everything else.

---

## 1. Product brief

### 1.1 Problem

Five Brothers Solutions Inc. builds commercial displays (store interiors, product display stands, brand signs,
event booths) in its own workshop from designs that the client approves. Today, requests, quotations, design
revisions, approvals, and progress are coordinated through manual methods and separate messaging channels, which
scatters project information, delays client decisions, and makes the current status and the approved design of a
project hard to confirm.

### 1.2 Goal

One web platform where the company and its clients coordinate each project from request to turnover, with
recorded decisions, automatic notifications and reminders, and a dashboard for management. The thesis evaluates
it by functional test cases, the System Usability Scale (SUS), and a before-and-after comparison of the time staff
need for seven coordination tasks (section 15.2).

### 1.3 Users

| Role | Who | Main jobs |
|---|---|---|
| Client (`client`) | People at a client company who coordinate a project; some are designated approvers | Submit requests, decide on quotations and design revisions, follow progress, download documents |
| Administrator or owner (`admin`) | Company owner | Oversee all projects, manage users and settings, override a stage with a reason |
| Account or project manager (`project_manager`) | Staff who handle client accounts | Create projects, designate approvers, upload and send quotations, chase pending decisions |
| Designer (`designer`) | Staff who prepare renders and spec sheets | Upload design revisions, read approvers' comments |
| Production staff (`production`) | Workshop and installation staff | Use the approved design, record production, delivery and installation, and turnover |

### 1.4 Scope

In scope: client and project records, project requests, quotation management (versions and decisions, not cost
computation), design revision tracking and approval, project progress tracking, the project document repository,
email and in-app notifications and reminders, the management dashboard, role-based access, an activity log, and
exports of activity counts for the evaluation.

Out of scope (do not build): 3D or AR visualization, CNC or workshop machine integration, kiosk features, online
payments, SMS, native mobile apps, AI chatbots, fabrication cost computation, inventory, payroll, HR, accounting.

### 1.5 Project lifecycle

```
Client request ──PR1/PR2──▶ [Request] ──quotation accepted (PR3)──▶ [Design]
[Design] ──all designated approvers approve revision (PR5)──▶ [Production]
[Production] ──PR7──▶ [Delivery and Installation] ──PR7──▶ [Turnover] (project completed)
Change after approval (PR8): [Production or Delivery and Installation] ──▶ back to [Design] until a new revision
is approved (and a revised quotation is accepted if the cost changes)
```

---

## 2. Architecture and stack

### 2.1 Why this stack

- **No third-party database.** SQLite is a file-based database built into Python and fully supported by Django.
  There is no account, server, or connection string to set up; `python manage.py migrate` creates it. It handles
  the load of one company and its clients comfortably. Because all access goes through the Django ORM, switching to
  PostgreSQL later is a configuration change (`DATABASE_URL`), not a rewrite.
- **Matches the thesis architecture** (Chapter 3, Figure 12): React front end, Django back end with a REST API,
  a relational database, file storage, a scheduled reminder task, and an email service.
- **One deployable unit.** In production, Django serves the built React app and the API from the same origin, so
  session cookies and CSRF work without CORS.

### 2.2 Components

| Layer | Choice | Notes |
|---|---|---|
| Language and framework | Python 3.12, Django 5.2 LTS | Custom user model from the first migration |
| API | Django REST Framework, django-filter | Session authentication; page-number pagination (20) |
| API schema (development) | drf-spectacular | `/api/schema/` and `/api/docs/` in development only |
| Database | SQLite (WAL mode) | `backend/data/fabrisee.sqlite3`; `DATABASE_URL` switches to PostgreSQL |
| Files | Django `FileField`, Pillow thumbnails | Images (JPG, PNG, WebP) and PDF; size limit setting (default 20 MB) |
| File type check | `filetype` package | Check content, not only the extension |
| Email | Database email backend + console (development); SMTP (production) | Every email is also saved in `EmailLog` |
| Scheduler | `manage.py run_scheduler` (loop) | Calls `send_due_reminders()` every `REMINDER_CHECK_MINUTES` (default 5) |
| Demo PDFs | `fpdf2` | Generates sample quotations and spec sheets for the demo data |
| Static files (production) | WhiteNoise | Serves the Vite build |
| App server (production) | gunicorn | |
| Frontend | React, TypeScript (strict), Vite | Path alias `@/` → `src/` |
| Styling and components | Tailwind CSS, shadcn/ui (Radix primitives), lucide-react | Follow the shadcn installation guide for Vite |
| Data fetching | TanStack Query | Query keys per resource; invalidate after mutations |
| Routing | React Router | Separate layouts for staff workspace, client portal, and sign-in |
| Forms | React Hook Form + Zod | Client-side checks mirror the backend; the backend decides |
| Dates | date-fns | Display in Asia/Manila; formats in section 11.7 |
| Toasts | sonner (shadcn) | |
| Tests | pytest, pytest-django, factory_boy, Vitest, Testing Library, Playwright | |
| Tooling | ruff, ESLint, Prettier, GitHub Actions | |
| Process manager (development) | honcho | Runs `Procfile.dev` |

Use the current stable versions and commit the lock files (`package-lock.json`; pinned `requirements*.txt`).

### 2.3 Request flow

```
Browser ──▶ Vite dev server :5173 ──/api, /admin──▶ Django :8000 ──▶ SQLite, media/
                                     (production: Django serves index.html and /static itself)
run_scheduler ──every 5 min──▶ send_due_reminders() ──▶ Notification + EmailLog (+ SMTP in production)
```

---

## 3. Repository layout

```
fabrisee/
├── CLAUDE.md
├── FABRISEE_BUILD_GUIDE.md
├── PROGRESS.md
├── README.md
├── Makefile
├── Procfile.dev                # web, vite, scheduler
├── .env.example
├── .gitignore  .editorconfig
├── .devcontainer/devcontainer.json
├── .github/workflows/ci.yml
├── docs/
│   ├── decisions/              # short ADRs: 0001-sqlite.md, ...
│   └── screenshots/            # desktop and mobile captures of key screens
├── backend/
│   ├── manage.py
│   ├── requirements.txt  requirements-dev.txt
│   ├── pytest.ini  ruff.toml
│   ├── config/
│   │   ├── settings/ (base.py, dev.py, test.py, prod.py)
│   │   ├── urls.py  wsgi.py  asgi.py
│   ├── apps/
│   │   ├── accounts/           # User, roles, auth API, permissions, privacy acknowledgment
│   │   ├── clients/            # Client
│   │   ├── projects/           # Project, ProjectApprover, StageUpdate, Document, next-step helper
│   │   ├── quotations/         # Quotation
│   │   ├── designs/            # DesignRevision, Approval
│   │   ├── notifications/      # Notification, EmailLog, notify(), reminders, run_scheduler
│   │   ├── activity/           # ActivityLog, CSV export
│   │   └── core/               # SystemSetting, file validation, SPA view, seed_demo, seed_scenarios
│   ├── data/                   # SQLite database (ignored by git)
│   └── media/                  # uploads (ignored by git)
└── frontend/
    ├── index.html  package.json  vite.config.ts  tsconfig*.json  components.json
    ├── e2e/                    # Playwright specs
    └── src/
        ├── main.tsx  App.tsx  router.tsx
        ├── styles/globals.css  # Tailwind and design tokens
        ├── lib/ (api.ts, auth.tsx, query.ts, format.ts, constants.ts)
        ├── components/ui/      # shadcn primitives
        ├── components/         # StageChip, StatusBadge, StageTracker, PageHeader, EmptyState, FileDropzone, ...
        ├── layouts/ (StaffLayout.tsx, PortalLayout.tsx, AuthLayout.tsx)
        └── features/
            ├── auth/ dashboard/ projects/ requests/ quotations/ revisions/
            ├── progress/ documents/ notifications/ clients/ admin/
```

---

## 4. Development environment

### 4.1 GitHub Codespaces (how the group runs the app without installing anything)

Create `.devcontainer/devcontainer.json` so that a codespace sets itself up and starts the app:

- Image `mcr.microsoft.com/devcontainers/python:3.12` with the Node feature (current Node LTS, 22 or newer).
- `postCreateCommand`: `make setup` (installs dependencies, migrates, seeds demo data).
- `postAttachCommand`: `make dev` (it runs in a terminal of the codespace, so the servers keep running and their
  logs stay visible).
- `forwardPorts`: `[5173, 8000]`; label 5173 "FabriSee" with `onAutoForward: openBrowser`; label 8000
  "Django API" with `onAutoForward: silent`.
- VS Code extensions: Python, Ruff, ESLint, Tailwind CSS IntelliSense, Prettier.

Group steps (put them in the README): repository page → **Code** → **Codespaces** → **Create codespace on main**
→ wait for the setup to finish → the FabriSee tab opens (or open port 5173 from the **Ports** tab) → sign in with a
demo account from the README. Stop the codespace when done, because personal accounts have a monthly free quota.
After merging a new pull request, open a fresh codespace (or run `git pull && make setup` in its terminal).

Codespaces gotchas (handle them in Milestone 0):

- `vite.config.ts`: `server.host = '0.0.0.0'`, `server.port = 5173`, `server.strictPort = true`,
  `server.allowedHosts = ['.app.github.dev', 'localhost', '127.0.0.1']`, and when `process.env.CODESPACES` is set,
  `server.hmr.clientPort = 443`. Proxy `/api`, `/admin`, and `/static/admin` to `http://127.0.0.1:8000`.
- Django development settings: `ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.app.github.dev']`,
  `CSRF_TRUSTED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173', 'https://*.app.github.dev']`.

### 4.2 Local machine (optional)

Install Python 3.12 and a current Node LTS, then `make setup` and `make dev`, and open `http://localhost:5173`.

### 4.3 Claude Code cloud sessions

The default network setting reaches the common package registries, so `pip install` and `npm install` work.
Install dependencies inside the session (`make setup`). Do not configure an environment setup script until
Milestone 0 is merged; if one is added later, it must be idempotent and must not fail the session start
(for example `bash scripts/cloud_setup.sh || true`). Playwright browsers may not be downloadable; then skip
`make e2e` and rely on CI.

### 4.4 Environment variables (`.env.example`)

| Variable | Development default | Purpose |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | Settings module |
| `SECRET_KEY` | generated placeholder | Required in production |
| `DEBUG` | `1` | `0` in production |
| `DATABASE_URL` | `sqlite:///backend/data/fabrisee.sqlite3` | PostgreSQL URL in production if wanted |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | see 4.1 | Comma-separated |
| `FRONTEND_URL` | `http://localhost:5173` | Links in emails |
| `EMAIL_BACKEND` | `apps.notifications.backends.DatabaseEmailBackend` | SMTP backend in production |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | empty | SMTP |
| `DEFAULT_FROM_EMAIL` | `FabriSee <no-reply@fabrisee.local>` | Sender |
| `REMINDER_CHECK_MINUTES` | `5` | Scheduler interval |
| `ALLOW_DEMO_SEED` | `1` | Must be `0` in production |
| `TIME_ZONE` | `Asia/Manila` | |

SQLite options in `base.py`: `"OPTIONS": {"init_command": "PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;",
"transaction_mode": "IMMEDIATE"}` when the engine is SQLite.

---

## 5. Data model

The entities follow the thesis ERD (Chapter 3, Figures 13 and 14). Fields marked *(impl.)* are implementation
details added here; list them in `PROGRESS.md` so the group can update the ERD in the thesis. All models have
`created_at` and `updated_at` unless stated. Use `TextChoices` for enums.

### 5.1 Accounts and clients

**User** (custom `AbstractUser`, email as the login): `email` (unique), `full_name`, `role` (`client`, `admin`,
`project_manager`, `designer`, `production`), `client` (FK Client, required if and only if `role = client`),
`phone`, `job_title` *(impl.)*, `is_active`, `privacy_acknowledged_at` *(impl., section 16)*, `last_login`.

**Client**: `company_name` (unique), `contact_person`, `email`, `phone`, `address`, `notes` (staff only),
`is_active`.

### 5.2 Projects

**Project**: `project_number` (unique, generated: `{prefix}-{year}-{seq:04d}`, prefix from settings, default
`FS`), `client` (FK), `title`, `project_type` (`store_interior`, `display_stand`, `brand_sign`, `event_booth`,
`other`), `location`, `target_date`, `dimensions` (text, for example "3 m × 6 m booth; 2.4 m height"),
`description`, `stage` (`request`, `design`, `production`, `delivery_installation`, `turnover`), `status`
*(impl.)* (`active`, `on_hold`, `cancelled`, `completed`), `manager` (FK User, project manager or admin),
`designer` *(impl.)* (FK User, nullable), `design_reopened` *(impl.)* (bool, PR8), `requires_requote`
*(impl.)* (bool, PR8), `created_by` (FK User).

**ProjectApprover**: `project`, `user` (must be an active user of the project's client); unique together.

**StageUpdate**: `project`, `from_stage`, `to_stage`, `remarks`, `updated_by`, `source` *(impl.)* (`rule`,
`manual`, `override`), `created_at`. Written for every stage change, including those made by rules.

**Document**: `project`, `doc_type` (`reference`, `quotation`, `render`, `spec_sheet`, `turnover`, `other`),
`file`, `original_name`, `size_bytes`, `content_type`, `thumbnail` *(impl.)*, `visible_to_client` (bool),
`uploaded_by`.

### 5.3 Quotations

**Quotation**: `project`, `version_no` (1, 2, 3 … per project), `amount` (Decimal, PHP), `file` (PDF),
`notes`, `status` (`draft`, `sent`, `accepted`, `returned`, `superseded`), `prepared_by`, `sent_at`,
`decided_by` (FK User, nullable), `decided_at`, `client_comment`, `decided_on_behalf` *(impl.)* (bool),
`decision_channel` *(impl.)* (`portal`, `email`, `phone`, `in_person`), `last_reminded_at` *(impl.)*.

### 5.4 Design revisions and approvals

**DesignRevision**: `project`, `revision_no` (1, 2, 3 … per project; shown as R1, R2 …), `render` (image or PDF),
`spec_sheet` (PDF or image, optional), `notes`, `status` (`pending_approval`, `changes_requested`, `approved`,
`superseded`), `uploaded_by`, `uploaded_at`, `locked_at`, `last_reminded_at` *(impl.)*.

**Approval**: `revision`, `approver` (FK User), `decision` (`approved`, `changes_requested`), `comment` (required
when changes are requested), `decided_on_behalf` *(impl.)*, `decision_channel` *(impl.)*, `created_at`; unique
together (`revision`, `approver`).

### 5.5 Notifications and activity

**Notification**: `user`, `project` (nullable), `event` (see 9.1), `title`, `message`, `link` (frontend path),
`is_read`, `read_at`, `created_at`.

**EmailLog** *(impl.)*: `to`, `subject`, `body_text`, `body_html`, `status` (`logged`, `sent`, `failed`),
`error`, `notification` (nullable), `created_at`.

**ActivityLog**: `actor` (nullable for system), `project` (nullable), `action` (enum, see 9.3), `details`
(JSON), `created_at`. Append-only.

**SystemSetting** *(impl.)* (single row): `company_name` (default "Five Brothers Solutions Inc."),
`project_number_prefix` (`FS`), `reminder_hours` (48), `max_upload_mb` (20), `quotation_decision_mode`
(`any_approver`), `updated_by`.

### 5.6 Integrity rules in the database

- Unique: `Project.project_number`; (`project`, `version_no`); (`project`, `revision_no`); (`revision`,
  `approver`); (`project`, `user`) for approvers.
- At most one quotation per project with status `sent`; at most one revision per project with status
  `pending_approval` (enforce in services; add conditional unique constraints where the database supports them).
- Approved revisions and accepted quotations are immutable: no file replacement or deletion (services reject it;
  the admin site marks the fields read-only).
- Deleting is soft for clients, users, and projects (`is_active` or `status = cancelled`); never cascade-delete
  history.

---

## 6. Process rules as services

All rules live in `services.py` functions. Views call services; services validate, change data inside
`transaction.atomic()`, write `StageUpdate` and `ActivityLog`, and call `notify()`. Raise a `RuleViolation`
(subclass of DRF `ValidationError`) with a code (for example `PR5_NOT_ALL_APPROVED`) and a plain-language message.

| Rule | Service function(s) | What it enforces | Tests |
|---|---|---|---|
| PR1 | `projects.services.submit_request(user, data, files)` | Required: project type, location, target date (not in the past), dimensions; reference files allowed (images or PDF) | TC1, TC2 |
| PR2 | `submit_request`, `create_project` | New project gets the next number and stage `request`; manager defaults to the first active project manager *(TO CONFIRM assignment rule)* | TC1 |
| PR3 | `quotations.services.create_quotation`, `send_quotation`, `decide_quotation` | New version supersedes earlier `sent`/`returned`/`draft` ones; only a designated approver (or staff recording on behalf, with channel) decides; accept → stage `design` if the stage was `request` (or clears `requires_requote` under PR8); return → comment required, status `returned`, new version needed | TC3 |
| PR4 | `designs.services.upload_revision` | Next revision number; earlier pending revision becomes `superseded`; allowed only when stage is `design` | TC5, TC8 |
| PR5 | `designs.services.record_decision` | Only designated approvers decide, once per revision, only on the current pending revision; changes requested → comment required, status `changes_requested`; all approved → status `approved`, `locked_at` set, stage `production` (or back to `production` after PR8 if no requote is pending) | TC4, TC5 |
| PR6 | `notifications.services.send_due_reminders(now)` | For every `sent` quotation and `pending_approval` revision older than `reminder_hours` whose last reminder is older than `reminder_hours`: remind each approver who has not decided, alert the manager, set `last_reminded_at`, log `reminder_sent` | TC6 |
| PR7 | `projects.services.change_stage(user, project, to_stage, remarks)` | Manual changes only `production → delivery_installation → turnover`, by production staff, the manager, or admin; turnover sets status `completed`; client users notified | TC10 |
| PR8 | `projects.services.reopen_design(user, project, reason, cost_changes)` | Allowed in `production` or `delivery_installation`; sets stage `design`, `design_reopened = True`, `requires_requote = cost_changes`; production cannot resume until a new revision is approved and, if required, a new quotation is accepted | add tests |
| PR9 | DRF permission classes, `scoped_queryset(user)` helpers, file download view | Clients see only their client's projects and only client-visible documents and sent quotations; staff actions per section 7 | TC7 |

**Admin override.** `projects.services.override_stage(admin, project, to_stage, reason)` allows any stage change
with a mandatory reason, writes `StageUpdate(source='override')`, and notifies the manager. Use it only for real
exceptions (for example a cancelled project).

**Next-step helper.** `projects.selectors.next_step(project, viewer)` returns a short sentence shown on project
headers and the client portal, for example:

| Situation | Staff text | Client text |
|---|---|---|
| Request, no quotation | "Prepare a quotation" | "We are preparing your quotation" |
| Quotation sent | "Waiting for the client to decide on quotation v2 (sent 2 days ago)" | "Please review quotation v2" (approvers) / "Waiting for your approver" |
| Design, no pending revision | "Upload the next design revision" | "Our designers are working on your design" |
| Revision pending | "R2 waiting for 1 of 2 approvers" | "Please review design R2" / "Waiting for other approvers" |
| Production | "In production since Nov 3" | "Your display is being built" |
| Delivery and Installation | "Delivery and installation in progress" | "Your display is being delivered and installed" |
| Turnover | "Turned over on Nov 20" | "Project completed" |

---

## 7. Roles and permissions

✓ = allowed; "own" = only projects of the user's client; "view" = read only.

| Action | Client | Admin | Project manager | Designer | Production |
|---|---|---|---|---|---|
| View projects | own | ✓ | ✓ | ✓ | ✓ |
| Submit a project request | own client | ✓ (on behalf) | ✓ (on behalf) | — | — |
| Edit project details, designate approvers | — | ✓ | ✓ | — | — |
| Manage clients | — | ✓ | ✓ | view | view |
| Manage users and settings | — | ✓ | — | — | — |
| Upload or send quotations | — | ✓ | ✓ | — | — |
| View quotations | own, sent ones only | ✓ | ✓ | view | — |
| Decide on a quotation | designated approvers | on behalf | on behalf | — | — |
| Upload design revisions | — | ✓ | ✓ | ✓ | — |
| Decide on a revision | designated approvers | on behalf | on behalf | — | — |
| View revisions and comments | own | ✓ | ✓ | ✓ | approved and history |
| Change stage (PR7) | — | ✓ | ✓ | — | ✓ |
| Reopen design (PR8) | request it (creates a notification to the manager) | ✓ | ✓ | — | — |
| Override stage | — | ✓ | — | — | — |
| Upload documents | reference files on own requests | ✓ | ✓ | ✓ | turnover documents |
| View or download documents | own, client-visible | ✓ | ✓ | ✓ | ✓ |
| Dashboard | client portal home | full | full | design view | production view |
| Activity log and exports | own project timeline | ✓ | ✓ (no exports) | project timeline | project timeline |
| Email outbox page | — | ✓ | — | — | — |

"On behalf" decisions require a channel (email, phone, in person) and are shown with a label such as
"Recorded by A. Villanueva on behalf of J. Cruz (phone)".

---

## 8. API

Base path `/api/`. JSON. Session authentication with CSRF (`X-CSRFToken` header from the `csrftoken` cookie).
Page-number pagination (`?page=`, 20 per page). Errors: `{"detail": "...", "code": "...", "fields": {...}}`.
Dates in ISO 8601 with time zone; money as decimal strings.

| Method and path | Purpose |
|---|---|
| `GET /api/auth/csrf/` | Set the CSRF cookie |
| `POST /api/auth/login/`, `POST /api/auth/logout/`, `GET /api/auth/me/` | Session sign-in, sign-out, current user with role and permissions |
| `POST /api/auth/privacy-ack/` | Record the privacy notice acknowledgment |
| `POST /api/auth/password-reset/`, `POST /api/auth/password-reset/confirm/` | Set or reset password (invitation flow) |
| `GET/POST /api/clients/`, `GET/PATCH /api/clients/{id}/` | Clients (staff) |
| `GET/POST /api/users/`, `PATCH /api/users/{id}/`, `POST /api/users/{id}/invite/` | Users (admin) |
| `GET /api/projects/` | List with filters `stage`, `status`, `client`, `q` (number, title, client), `needs_action=1`, `overdue=1` |
| `POST /api/projects/requests/` | Submit a request (PR1, PR2); multipart with reference files |
| `GET/PATCH /api/projects/{id}/` | Detail (includes `next_step`, current quotation, current and approved revision) |
| `PUT /api/projects/{id}/approvers/` | Set designated approvers |
| `POST /api/projects/{id}/stage/` | Change stage (PR7) |
| `POST /api/projects/{id}/reopen-design/` | PR8 |
| `POST /api/projects/{id}/override-stage/` | Admin override |
| `GET /api/projects/{id}/timeline/` | Stage updates and activity for the project |
| `GET/POST /api/projects/{id}/quotations/` | List and create (draft or upload-and-send) |
| `POST /api/quotations/{id}/send/`, `POST /api/quotations/{id}/decision/` | Send; accept or return (PR3) |
| `GET/POST /api/projects/{id}/revisions/` | List and upload (PR4) |
| `POST /api/revisions/{id}/decision/` | Approve or request changes (PR5) |
| `POST /api/revisions/{id}/remind/`, `POST /api/quotations/{id}/remind/` | Manual reminder (logged) |
| `GET/POST /api/projects/{id}/documents/` | Document repository |
| `GET /api/files/{kind}/{id}/` | Permission-checked download or inline view (`?inline=1`); kinds: document, quotation, render, spec |
| `GET /api/notifications/`, `POST /api/notifications/{id}/read/`, `POST /api/notifications/read-all/` | In-app notifications; `unread_count` in the list response |
| `GET /api/dashboard/` | Counts by stage, pending decisions with waiting time, overdue items, due this week, recent activity |
| `GET /api/approvals/pending/` | All pending quotation and revision decisions (staff) |
| `GET/PATCH /api/settings/` | System settings (admin) |
| `GET /api/email-outbox/` | Email log (admin) |
| `GET /api/reports/activity.csv?from=&to=`, `GET /api/reports/summary/?from=&to=` | Activity export and counts for Chapter 4 (admin) |

---

## 9. Notifications, email, and reminders

### 9.1 Events (thesis Table 9, plus implementation events)

| Event code | Trigger | Recipients | In-app | Email |
|---|---|---|---|---|
| `request_submitted` | PR2 | Manager (or all project managers if none assigned) | ✓ | ✓ |
| `quotation_sent` | Quotation sent | Client users of the project; approvers marked "decision needed" | ✓ | ✓ |
| `quotation_decided` | Accepted or returned | Manager; designer when accepted | ✓ | ✓ |
| `revision_uploaded` | PR4 | Designated approvers ("please review"), manager | ✓ | ✓ |
| `revision_changes_requested` | PR5 | Designer, manager | ✓ | ✓ |
| `revision_approved` | PR5, locked | Designer, manager, production staff, client users | ✓ | ✓ |
| `decision_reminder` | PR6 | Each approver who has not decided | ✓ | ✓ |
| `decision_overdue_alert` | PR6 | Manager | ✓ | ✓ |
| `stage_changed` | PR7, override | Client users, manager | ✓ | ✓ |
| `project_turned_over` | PR7 turnover | Client users, admin | ✓ | ✓ |
| `design_reopened` | PR8 | Designer, manager, production staff, client users | ✓ | ✓ |
| `change_requested_by_client` | Client asks for a change after approval | Manager | ✓ | ✓ |

Rules: never notify the person who caused the event; group a burst of the same event to the same user within one
minute into one notification; every notification has a deep link (for example `/portal/projects/12/designs`).

### 9.2 Email

- `notify()` creates the `Notification` rows and sends one email per recipient through Django's email framework.
  The development backend `DatabaseEmailBackend` stores each message in `EmailLog` and prints it to the console;
  production uses SMTP and still writes `EmailLog` rows with the delivery status.
- Templates in `apps/notifications/templates/emails/`: plain text and simple HTML with the FabriSee wordmark, a
  short message, the project number and title, one button linking to `FRONTEND_URL` + path, and a footer with the
  company name.
- Subject format: `[FabriSee] FS-2026-0007 · Design R2 is waiting for your approval`.

### 9.3 Activity log actions

`request_submitted`, `project_created`, `project_updated`, `approvers_changed`, `quotation_created`,
`quotation_sent`, `quotation_accepted`, `quotation_returned`, `revision_uploaded`, `revision_superseded`,
`revision_approved_by`, `revision_changes_requested_by`, `revision_locked`, `stage_changed`, `stage_overridden`,
`design_reopened`, `document_uploaded`, `reminder_sent`, `overdue_alert_sent`, `user_login`, `settings_changed`.
These counts feed the Chapter 4 export (section 15.3).

### 9.4 Reminders (PR6)

`run_scheduler` loops forever: call `send_due_reminders(timezone.now())`, sleep `REMINDER_CHECK_MINUTES`. It must
be safe to run twice at the same time (re-check `last_reminded_at` inside the transaction). Add
`manage.py send_due_reminders` for cron. The settings page shows the threshold and the time of the last check.

---

## 10. Screens and navigation

### 10.1 Sign-in and first login

- **Sign-in page** (`/login`): split layout. Left panel (hidden on mobile): blueprint-blue background with a faint
  grid pattern, the FabriSee wordmark, the line "Client coordination for custom fabrication projects", and three
  short benefit lines with icons. Right panel: email, password, "Sign in", "Forgot password?". After sign-in, staff
  go to `/app`, clients to `/portal`.
- **Privacy notice** (first login): a dialog with a short notice on what personal data FabriSee keeps and why
  (project coordination), who can see it, and how to ask for corrections; the user must acknowledge it once
  (section 16).

### 10.2 Staff workspace (`/app`)

Layout: left sidebar (dark slate) with the wordmark, navigation, and the user menu; top bar with global search
(project number, title, or client), a "New request" button, and the notification bell with the unread count.
On small screens the sidebar becomes a slide-over menu.

Navigation: Dashboard · Projects · Approvals · Clients · Notifications · (admin) Users · Settings · Email outbox.

| Screen | Content and behavior |
|---|---|
| **Dashboard** `/app` | Greeting and date. KPI cards: Active projects, Waiting for client decisions, Overdue items, Due in the next 7 days (each clickable to a filtered list). "Needs attention" list (pending decisions with waiting time and a "Remind" button; projects past their target date). Projects by stage: five columns with counts and project cards (number, title, client, target date, next step); read-only, because stage changes follow the rules. Recent activity feed. Role variants: designers see "Revisions to prepare" first; production sees "Approved and ready to build". |
| **Projects list** `/app/projects` | Table on desktop, cards on mobile: number, title, client, type, stage chip, next step, target date (red if overdue), manager. Filters: stage, status, client, type, "needs action", "overdue"; search; sort by target date or last update. |
| **Project detail** `/app/projects/:id` | Header: number, title, client, stage chip, status, target date, manager, designer; the five-step stage tracker with dates; the next-step sentence; primary action for the viewer's role (for example "Upload revision", "Send quotation", "Mark as delivered and installed"). An **Approved design** card at the top whenever a locked revision exists (thumbnail, R number, approval date, download render and spec sheet). Tabs: **Overview** (details, dimensions, location, description, designated approvers with edit), **Quotations**, **Design revisions**, **Progress**, **Documents**, **Activity**. |
| **Quotations tab** | Version list (v1, v2 …) with status badges, amount (₱), sent date, decision, decided by and when, comment. "New quotation" dialog: amount, PDF upload, notes, "Save draft" or "Upload and send". "Record decision on behalf" (staff) with channel. |
| **Design revisions tab** | Left: revision list (R3, R2, R1) with status and date. Right: large viewer (image with zoom and full-screen; PDF inline), spec sheet link, the uploader's notes, and the **approvals panel** listing each designated approver with their decision, time, and comment. Approvers see "Approve" and "Request changes" (comment required). Locked revisions show a lock badge and "Approved by all designated approvers on …". Upload dialog: render (drag and drop), optional spec sheet, notes. Optional polish: compare two revisions side by side. |
| **Progress tab** | Vertical timeline of stage updates (who, when, remarks; rule-driven changes labeled), and the allowed next stage button with remarks (PR7). "Reopen design" (PR8) with reason and "cost changes" checkbox. |
| **Documents tab** | Grouped by type; upload with type and "visible to client"; preview images and PDFs; download. |
| **Activity tab** | Chronological activity log of the project. |
| **Approvals** `/app/approvals` | All pending quotation and revision decisions: project, item, approvers still pending, waiting time, last reminder, "Remind now". |
| **Clients** `/app/clients`, `/app/clients/:id` | Client list and detail with contacts (client users), their projects, and "Invite user". |
| **New request (staff)** | Same form as the client's, plus client selection and "on behalf of" contact. |
| **Notifications** `/app/notifications` | Full list with filters (unread, type); mark all read. |
| **Users** (admin) | Staff and client users, roles, active state, invite or resend invite, deactivate. |
| **Settings** (admin) | Company name, project number prefix, reminder threshold (hours), upload size limit, quotation decision mode, last reminder check. |
| **Email outbox** (admin) | Email log with recipient, subject, time, status, and a preview of the body; shows that notifications work without real email. |

### 10.3 Client portal (`/portal`)

Layout: top bar with the wordmark, "My projects", "New request", the notification bell, and the user menu; on
mobile a bottom navigation bar. Friendlier tone and larger text (16 px base).

| Screen | Content and behavior |
|---|---|
| **My projects** `/portal` | "Action needed" section first (quotations and revisions waiting for this user's decision, each with a large button). Then project cards: title, number, a five-step tracker, next step, target date, last update. Empty state with "Submit your first request". |
| **New request** `/portal/requests/new` | Stepped form on mobile (1 Project, 2 Size and location, 3 Files, 4 Review): project type (cards with icons), title, location, target date, dimensions (with an example hint), description, reference files (drag and drop, images or PDF). PR1 errors inline. Success screen shows the new project number. |
| **Project** `/portal/projects/:id` | Big stage tracker and next step; tabs: **Summary**, **Quotation** (current version with PDF viewer and Accept or Return with comments for approvers; earlier versions collapsed), **Designs** (current revision viewer with Approve or Request changes for approvers, list of who still needs to decide, history), **Progress** (timeline in plain language), **Documents** (client-visible files). |
| **Notifications** `/portal/notifications` | Same pattern as staff. |

### 10.4 States every screen needs

Loading (skeletons matching the layout), empty (icon, one sentence, primary action), error (plain message and
"Try again"), no permission (403 page with a way back), not found (404). Disable buttons while a mutation runs;
show a toast on success; keep form input on failure.

---

## 11. Visual design system

### 11.1 Direction

Calm, precise, and crafted, like a clean blueprint on a well-organized workshop bench. Plenty of whitespace,
clear hierarchy, few colors with clear meanings, and design files shown large on a neutral canvas. Professional
for staff, reassuring and simple for clients.

### 11.2 Color tokens (light theme; contrast ratios checked)

| Token | Value | Use |
|---|---|---|
| `--background` | `#F8FAFC` | Page |
| `--card` | `#FFFFFF` | Cards, dialogs, tables |
| `--foreground` | `#0F172A` | Body text (17:1 on page) |
| `--muted-foreground` | `#64748B` | Secondary text (4.6:1 on page, 4.8:1 on white) |
| `--border` | `#E2E8F0` | Card and table borders (decorative) |
| `--input` | `#8291A5` | Form control borders (3.2:1, meets the 3:1 rule for controls) |
| `--ring` | `#2563EB` | Focus ring, 2 px with 2 px offset (5.2:1) |
| `--primary` / `--primary-foreground` | `#1E40AF` / `#FFFFFF` | Primary buttons, active navigation (8.7:1) |
| `--primary-hover` | `#1E3A8A` | |
| `--link` | `#1D4ED8` | Links (6.7:1) |
| `--sidebar` / `--sidebar-foreground` | `#0F172A` / `#CBD5E1` | Staff sidebar (12:1); active item `#1E293B` with white text and a 3 px blue bar |
| `--accent-brand` | `#C2410C` | Workshop orange for the logo mark and small brand accents only (5.2:1 as text) |

Status badges (text on tint, all at least 4.5:1): pending `#B45309` on `#FFFBEB`; approved and locked
`#15803D` on `#F0FDF4`; changes requested `#B91C1C` on `#FEF2F2`; sent `#1D4ED8` on `#EFF6FF`; draft and superseded
`#475569` on `#F1F5F9`.

Stage chips and tracker colors: Request `#475569` on `#F1F5F9`; Design `#4338CA` on `#EEF2FF`; Production
`#C2410C` on `#FFF7ED`; Delivery and Installation `#0E7490` on `#ECFEFF`; Turnover `#15803D` on `#F0FDF4`. Always
show the stage name; the tracker also uses icons (Inbox, PenTool, Hammer, Truck, CircleCheck from lucide).

Dark theme: optional in Milestone 9; define the same tokens under `.dark` and re-check contrast.

### 11.3 Typography

Inter Variable (Fontsource, self-hosted). Staff workspace base 14 px, client portal base 16 px. Scale: 12, 14, 16,
18, 20, 24, 30 px. Weights 400 body, 500 labels and table headers, 600 headings, 700 only for the wordmark and KPI
numbers. Line height 1.5 for text, 1.25 for headings. Tabular numerals for amounts, dates, project numbers, and
counts. Sentence case for headings and buttons.

### 11.4 Layout and spacing

4 px grid. Page padding 24 px (desktop) and 16 px (mobile); content max width 1280 px; card padding 20–24 px;
16–24 px gaps between cards. Radius 8 px for buttons and inputs, 12 px for cards and dialogs, full for chips.
Shadows: none or `shadow-sm` on cards, `shadow-lg` on dialogs and menus. Sticky table headers; sticky project
header on scroll (compact version).

### 11.5 Components (build once in `src/components/`, reuse everywhere)

`AppLogo` (wordmark: "Fabri" in foreground, "See" in primary, with a small orange square mark that has one cut
corner), `PageHeader`, `StageChip`, `StatusBadge`, `StageTracker` (horizontal on desktop, vertical on mobile, with
dates), `KpiCard`, `ProjectCard`, `DataTable` (sorting, empty state), `FilterBar`, `FileDropzone` (drag and drop,
type and size checks, previews), `FilePreview` (image zoom, PDF inline, download), `RevisionViewer`,
`ApprovalPanel`, `Timeline`, `ActivityFeed`, `EmptyState`, `ConfirmDialog`, `NotificationBell` (popover with the
latest ten and "View all"), `UserMenu`, `SearchCommand` (command palette with `Ctrl+K`), `Money`, `RelativeTime`.

### 11.6 Motion and interaction

150–200 ms ease-out transitions for hover, popovers, and dialogs; no decorative animation; respect
`prefers-reduced-motion`. Optimistic UI only for marking notifications read; everything else waits for the server.

### 11.7 Content and formats

- Dates: "Nov 11, 2026"; with time "Nov 11, 2026, 3:45 PM"; relative within 7 days ("2 days ago") with the
  exact time in a tooltip. Time zone Asia/Manila.
- Money: "₱125,000.00". Project numbers in a monospaced-looking tabular style: `FS-2026-0007`. Revisions: "R2".
- Write plainly: "Waiting for your approval", "Approved by all designated approvers", "Changes requested by J.
  Cruz". Error messages say what happened and what to do.

### 11.8 Accessibility

WCAG 2.1 AA: contrast as above, visible focus, keyboard access for every action (dialogs trap focus, `Esc`
closes), labels on all inputs, `aria-label` on icon-only buttons, status never shown by color alone, images with
`alt` text (render alt: "Design R2 of FS-2026-0007"), targets at least 40 px on touch screens.

### 11.9 UI quality checklist (run before every pull request)

- Spacing and alignment follow the grid; no element touches a container edge without padding.
- Text never overflows; long names truncate with a tooltip.
- The same thing looks the same everywhere (chips, badges, buttons, dates, money).
- Every screen has loading, empty, and error states.
- Works at 390 px width with no horizontal scrolling (tables become cards).
- No console errors or warnings; no layout shift when data loads.

---

## 12. Demo data

`manage.py seed_demo` (runs only when `ALLOW_DEMO_SEED=1`) creates a realistic, fully fictitious dataset; dates are
relative to the day it runs so the dashboard always shows pending and overdue items. `manage.py reset_demo` deletes
the database and media and seeds again. Generate images with Pillow (simple flat drawings of booths, counters,
signs, and display stands with a "DEMO" corner label) and PDFs with fpdf2 (quotation and spec sheet layouts with
"Sample document" in the footer). Do not use real brand names, logos, or photos.

**Demo password for every account:** `FabriSee@2026` (demo only; printed by the seed command and listed in the
README with a warning that production must not run the seed).

| Account | Role | Notes |
|---|---|---|
| `owner@fabrisee.test` — Teresa Lim | admin | Owner |
| `pm@fabrisee.test` — Andrea Villanueva | project_manager | Manager of most projects |
| `designer@fabrisee.test` — Paolo Garcia | designer | |
| `production@fabrisee.test` — Ramon Dizon | production | Production lead |
| `joanna@aurelia.test`, `mark@aurelia.test` | client | Aurelia Audio Labs; both are designated approvers |
| `liza@tindahantech.test` | client | Tindahan Tech PH |
| `nico@kapetirya.test` | client | Kapetirya Coffee House |
| `bianca@lunaria.test`, `ella@lunaria.test` | client | Lunaria Skin Studio; Bianca approves, Ella only views |

Projects (one per situation the demo must show):

1. Aurelia Audio Labs — "Experience counter and brand wall" — Design; R2 pending; Joanna approved, Mark pending for
   3 days (overdue reminder visible).
2. Tindahan Tech PH — "Product display stands (set of 6)" — Request; quotation v1 sent 3 days ago, no decision.
3. Kapetirya Coffee House — "Café counter and menu signage" — Production; R3 approved and locked; R1, R2 in history.
4. Lunaria Skin Studio — "Trade fair booth, 3 m × 6 m" — Delivery and Installation.
5. Aurelia Audio Labs — "Window display refresh" — Turnover (completed) with turnover documents.
6. Tindahan Tech PH — "Illuminated brand sign" — Request; new, no quotation yet.
7. Kapetirya Coffee House — "Pop-up booth for weekend market" — Design; R1 changes requested with comments, R2
   not yet uploaded.
8. Lunaria Skin Studio — "End-cap product display" — Request; quotation v1 returned with comments, v2 in draft.

Also seed: stage updates with realistic dates, notifications (some unread for each demo user), email log entries,
and activity entries.

`manage.py seed_scenarios --set A|B` (Milestone 9) creates the practice client "Practice Client (Training)" and the
sample projects used for the timed posttest tasks (section 15.2), and `--remove` deletes them.

---

## 13. Testing and quality

### 13.1 Backend

pytest + pytest-django + factory_boy, with factories for every model. Service tests for every rule (passing and
failing paths), permission tests per role for every endpoint group, and API tests for the main flows. Run on SQLite
in memory. Target at least 85% line coverage for `services.py` and permissions.

The sample test cases of the thesis (Chapter 3, Table 10) must exist as automated tests with these names:

| Test | Thesis test case |
|---|---|
| `test_tc1_request_with_all_required_fields_creates_project` | TC1: request saved, project number, stage Request, manager notified |
| `test_tc2_request_without_target_date_is_rejected` | TC2: PR1 |
| `test_tc3_returned_quotation_saves_comment_and_allows_new_version` | TC3: PR3 |
| `test_tc4_all_approvers_approve_locks_revision_and_moves_to_production` | TC4: PR5 |
| `test_tc5_change_request_marks_revision_and_allows_next_revision` | TC5: PR5, PR4 |
| `test_tc6_pending_revision_beyond_threshold_sends_reminder_and_alert` | TC6: PR6 |
| `test_tc7_client_cannot_open_other_clients_project` | TC7: PR9 (API and file download) |
| `test_tc8_production_sees_approved_revision_first` | TC8 |
| `test_tc9_dashboard_shows_stage_counts_pending_and_overdue` | TC9 |
| `test_tc10_stage_change_records_actor_and_notifies_client` | TC10: PR7 |

### 13.2 Frontend

Vitest + Testing Library for components with logic (`StageTracker`, `ApprovalPanel`, `FileDropzone`, request form
validation, permission-based button visibility). ESLint and `tsc --noEmit` must pass.

### 13.3 End to end (Playwright)

Specs: (1) client submits a request; (2) manager uploads and sends a quotation; client accepts; (3) designer uploads
R1; one approver requests changes; designer uploads R2; both approve; project moves to Production; (4) production
moves to Delivery and Installation and Turnover; client sees the timeline; (5) client cannot open another client's
project. Add a `screenshots.spec.ts` that captures the key screens at 1440 × 900 and 390 × 844 into
`docs/screenshots/`.

### 13.4 Continuous integration

`.github/workflows/ci.yml` on push and pull request: backend job (ruff, pytest with coverage), frontend job
(npm ci, lint, typecheck, Vitest, build), e2e job (install Playwright browsers, start both servers with demo data,
run specs, upload screenshots and the report as artifacts).

---

## 14. Milestones

Each milestone ends with: `make test` green, the app running with `make dev`, `PROGRESS.md` updated, and a pull
request. Suggested sessions: **Session 1 = M0–M2**, **Session 2 = M3–M5**, **Session 3 = M6–M8**,
**Session 4 = M9**, **Session 5 = M10** (when the group decides on hosting).

### M0 — Foundation and developer experience

Tasks: repository layout (section 3); Django project with split settings, custom user model, DRF, SQLite with WAL,
`dj-database-url`, WhiteNoise, drf-spectacular (development); React + TypeScript + Vite app with Tailwind,
shadcn/ui, Inter, design tokens (section 11.2), React Router, TanStack Query; Vite proxy; Makefile, `Procfile.dev`,
`.env.example`, `.gitignore`, `.editorconfig`; devcontainer (section 4.1); CI workflow; README (what FabriSee is, how
to open it in Codespaces, demo accounts, commands); `PROGRESS.md`; `docs/decisions/0001-sqlite-and-django.md`;
health endpoint `GET /api/health/`.

Acceptance: `make setup && make dev` serves the React app on 5173 and the API on 8000; the frontend shows a styled
placeholder page that calls `/api/health/`; CI passes; a codespace starts the app without manual steps.

### M1 — Data model, authentication, roles, demo data

Tasks: all models in section 5 with migrations and admin pages (read-only history fields); `SystemSetting`;
project number generator; session auth endpoints; role-based redirect; permission classes and scoped querysets;
`notify()` stub that writes `Notification` and `EmailLog`; `seed_demo` and `reset_demo` with generated images and
PDFs; privacy acknowledgment endpoint.

Acceptance: every demo account signs in and lands on the right area; `/api/auth/me/` returns role and permissions;
seeded data visible in Django admin; model and permission tests pass.

### M2 — App shell, design system, read-only views

Tasks: sign-in page and privacy dialog; `StaffLayout` and `PortalLayout`; the shared components in section 11.5;
dashboard (read-only data from `/api/dashboard/`); projects list with filters and search; project detail with header,
stage tracker, next step, approved design card, and all tabs reading seeded data; client portal home and project
page (read only); notification bell with real unread counts; 403 and 404 pages; first screenshots.

Acceptance: a reviewer can sign in as each demo user and browse realistic data on desktop and phone sizes; the UI
quality checklist (11.9) passes; screenshots committed.

### M3 — Requests, projects, approvers, documents (PR1, PR2, PR9)

Tasks: client request form (stepped on mobile) with file upload; staff "new request on behalf"; edit project
details; designate approvers; document repository with upload, preview, client visibility; permission-checked file
view; thumbnails; activity entries and notifications (`request_submitted`).

Acceptance and tests: TC1, TC2, TC7 pass; uploading a disallowed file type or an oversized file shows a clear
error; a client never sees another client's project or a staff-only document (API and UI).

### M4 — Quotations (PR3)

Tasks: quotation versions (draft, upload and send), PDF viewer, accept or return with comment, record decision on
behalf, supersede logic, stage change to Design on acceptance, notifications, activity.

Acceptance and tests: TC3; accepting moves Request → Design and shows in the timeline; returning requires a comment
and enables "New version"; only designated approvers see decision buttons.

### M5 — Design revisions and approvals (PR4, PR5)

Tasks: upload revision (render and spec sheet), revision list and viewer, approvals panel, approve or request
changes, locking, Approved design card, supersede logic, notifications (`revision_uploaded`,
`revision_changes_requested`, `revision_approved`), optional side-by-side compare.

Acceptance and tests: TC4, TC5, TC8; a locked revision cannot be changed or deleted by anyone; the project moves to
Production only after all designated approvers approve.

### M6 — Progress tracking (PR7, PR8, override)

Tasks: stage change actions with remarks for allowed transitions; timeline; turnover with documents and completed
status; reopen design with "cost changes" (PR8) and the blocks it implies; client "request a change"; admin
override with reason.

Acceptance and tests: TC10; PR8 tests (production cannot resume until a new revision is approved and, if needed, a
quotation accepted); clients see plain-language progress.

### M7 — Notifications, email, reminders (PR6)

Tasks: notification list pages, bell popover, read state, grouping; email templates (text and HTML); database email
backend; Email outbox page; `send_due_reminders` and `run_scheduler`; manual "Remind now"; Approvals page; settings
page with the threshold; invitation and password-reset flow for new users.

Acceptance and tests: TC6; changing the threshold changes when reminders fire (test with frozen time); every event in
9.1 produces the right recipients; reminders are not sent twice within the threshold.

### M8 — Management dashboard and reports

Tasks: final dashboard (KPIs, needs attention, stage columns, due this week, activity feed, role variants); global
search command palette; activity CSV export and summary counts by date range (section 15.3).

Acceptance and tests: TC9; numbers on the dashboard match the database for the demo data; export opens in a
spreadsheet with one row per activity.

### M9 — Polish, accessibility, end-to-end tests, evaluation support

Tasks: run the UI quality checklist on every screen; accessibility pass (keyboard, focus, labels, contrast); mobile
refinements of the client portal; empty, loading, and error states everywhere; performance (pagination, image
thumbnails, query counts); Playwright specs and screenshots; optional dark theme; `seed_scenarios` for the timed
tasks; README and in-app help text.

Acceptance: all e2e specs pass in CI; screenshots updated; no console errors; the group can run the full demo script
(section 15.4) in under ten minutes.

### M10 — Deployment (only when the group chooses hosting)

Tasks: production settings, Dockerfile (Node build stage, Python runtime with gunicorn), persistent volume for
`backend/data` and `backend/media`, environment variables, HTTPS, SMTP, daily backup command for the SQLite file
(`sqlite3 ... ".backup ..."`) and media, `send_due_reminders` via cron or the scheduler process, deployment guide in
`docs/deployment.md`.

---

## 15. Thesis alignment

### 15.1 Objectives

| Thesis objective | Where it is met |
|---|---|
| 1. Design a client portal and staff workspace following the project workflow | Sections 10.2–10.3; M2–M3 |
| 2. Implement records, quotations, revision tracking and approval, progress tracking, document repository, management dashboard | M3–M6, M8 |
| 3. Integrate workflow automation (notifications and reminders) | Section 9; M4–M7 |
| 4. Validate functionality and usability | Section 13 (TC1–TC10 automated); SUS is collected outside the app |
| 5. Evaluate efficiency with task completion times | Section 15.2 features; `seed_scenarios`; exports in 15.3 |

### 15.2 The seven timed tasks (Chapter 3, Table 12) and the features that make them fast

| Task | Feature in FabriSee |
|---|---|
| T1 Record a new request | Request form with required fields and file drop; staff "on behalf" form |
| T2 Send a quotation | "Upload and send" in one dialog; automatic notification |
| T3 Send a revision for approval | Upload revision; approvers notified automatically |
| T4 Record a client decision | Clients decide in the portal; staff "record on behalf"; designer notified automatically |
| T5 Find the approved design | Approved design card at the top of every project; global search |
| T6 Answer a status inquiry | Stage tracker and next-step sentence; clients can see it themselves |
| T7 Summarize pending items | Dashboard "Needs attention" and Approvals page |

### 15.3 Data for Chapter 4

The activity export (admin) gives, for a date range, one row per activity (time, actor role, project, action) and a
summary sheet with counts of requests, quotations sent, quotation decisions, revisions uploaded, approvals, change
requests, stage changes, notifications, reminders, and overdue alerts. This supports the "activity log" summary in
the Chapter 3 statistical treatment.

### 15.4 Demo script for the group and panel (ten minutes)

1. Sign in as `liza@tindahantech.test`; submit a request (try leaving the target date empty to show PR1).
2. Sign in as `pm@fabrisee.test`; see the new request on the dashboard; upload and send a quotation.
3. Back as Liza; accept the quotation; the project moves to Design.
4. As `designer@fabrisee.test`; upload R1. As the client, request changes; as the designer, upload R2; approve as
   the client; the project moves to Production and R2 is locked.
5. As `production@fabrisee.test`; mark Delivery and Installation, then Turnover; the client sees the timeline.
6. As `owner@fabrisee.test`; show the dashboard, the Approvals page, the Email outbox, and the activity export.
7. Show the overdue reminder on the Aurelia project (PR6).

---

## 16. Security and data privacy

The thesis commits to the Data Privacy Act of 2012 (transparency, legitimate purpose, proportionality; appropriate
organizational, physical, and technical safeguards). In the app:

- Role-based access in the API and scoped querysets (PR9); files only through permission-checked views; no public
  media URLs in production.
- Django's password hashing; session cookies `HttpOnly`, `Secure` and `SameSite=Lax` in production; CSRF on all
  unsafe requests; DRF throttling on login (for example 10 per minute per IP) and password reset.
- File checks by content type and size; images re-saved through Pillow for thumbnails; filenames randomized on disk.
- Collect only what coordination needs (no birthdays, IDs, or payment details); staff-only notes never reach client
  endpoints.
- Privacy notice acknowledged at first login (`privacy_acknowledged_at`); text in `apps/accounts/privacy.md`
  *(the group should review the wording)*.
- Activity log is append-only; admin actions are logged.
- Production: `DEBUG=0`, strong `SECRET_KEY`, HTTPS only, `ALLOW_DEMO_SEED=0`, regular backups.
- Repository: no secrets or real data. Consider making the GitHub repository private because it names the partner
  company.

---

## 17. Deployment (later)

Not needed to try the app (use Codespaces). When the group needs a stable URL for the use period with real staff and
clients, choose one of these and do M10:

1. **A small virtual private server with Docker** — keeps SQLite and uploads on the server's disk; cheapest and
   simplest to reason about; needs HTTPS (for example with Caddy) and backups.
2. **A platform-as-a-service with a persistent volume** — the same Docker image; the volume holds `data/` and
   `media/`.
3. **Managed PostgreSQL** — set `DATABASE_URL`; still keep uploads on a persistent volume or object storage.

Whatever the host, the database must survive restarts (the use period lasts weeks), reminders must run on a
schedule, and outgoing email must be allowed by the host.

---

## 18. Working agreement and session prompts

### 18.1 Rules for every session

- Start by reading `CLAUDE.md`, this guide, and `PROGRESS.md`; state the plan for the session in `PROGRESS.md`.
- Work on one milestone at a time; commit in small steps with clear messages.
- Keep business rules in services and cover them with tests before polishing the UI.
- Run the app and look at what you built (screenshots at desktop and phone sizes when possible); fix what looks off.
- Never invent company facts. Use Appendix A defaults, mark them `TO CONFIRM`, and list them for the group.
- End the session with: tests green, app running, `PROGRESS.md` updated, and a pull request that has a summary, how
  to try it (demo accounts and steps), screenshots, and questions for the group.

### 18.2 `PROGRESS.md` format

```
# FabriSee progress
## Status
Current milestone: M2 (in progress) · Last updated: 2026-11-12
## Done
- M0 Foundation — PR #1
## Next
- ...
## Decisions
- 2026-11-11 SQLite with WAL as the database (docs/decisions/0001)
## Implementation details to reflect in the thesis
- Project.designer field (not in the thesis ERD)
## Questions for the group
- Reminder threshold: is 48 hours right?
## Known issues
- ...
```

### 18.3 Session prompts (paste one into Claude Code)

**Session 1 (M0–M2).**
> Read CLAUDE.md and FABRISEE_BUILD_GUIDE.md in this repository. Complete Milestones M0, M1, and M2 as specified:
> set up the project structure and the development environment (including the Codespaces dev container), build the
> data model with authentication, the five roles, and the demo data, and build the sign-in page, the staff workspace
> and client portal layouts, the design system components, and the read-only dashboard, project list, and project
> pages using the seeded data. Follow the definition of done, keep PROGRESS.md updated, commit in small steps, and
> open a pull request at the end with a summary, how to try it, screenshots if you can take them, and questions for
> the group.

**Session 2 (M3–M5).**
> Read CLAUDE.md, FABRISEE_BUILD_GUIDE.md, and PROGRESS.md. Complete Milestones M3, M4, and M5: project requests
> with file uploads, approvers and documents, quotations with versions and decisions, and design revisions with
> approvals and locking. Implement process rules PR1 to PR5 and PR9 in the backend services with tests TC1 to TC5,
> TC7, and TC8, then build the screens. Follow the definition of done and open a pull request at the end.

**Session 3 (M6–M8).**
> Read CLAUDE.md, FABRISEE_BUILD_GUIDE.md, and PROGRESS.md. Complete Milestones M6, M7, and M8: progress tracking
> with PR7, PR8, and the admin override; notifications, email templates, the Email outbox, reminders with the
> scheduler (PR6), and the invitation flow; and the final management dashboard, global search, and activity exports.
> Add tests TC6, TC9, and TC10 and the PR8 tests. Follow the definition of done and open a pull request at the end.

**Session 4 (M9).**
> Read CLAUDE.md, FABRISEE_BUILD_GUIDE.md, and PROGRESS.md. Complete Milestone M9: run the UI quality checklist and
> an accessibility pass on every screen, refine the mobile client portal, add the Playwright specs and screenshots,
> add seed_scenarios for the timed tasks, and update the README. Fix every issue you find and open a pull request.

**Feedback prompt (any time).**
> Read CLAUDE.md and PROGRESS.md. Here is feedback from the group after trying the app: [list]. Fix these, keep
> all tests passing, and open a pull request that explains each change.

---

## Appendix A. Values to confirm with the company

| Item | Default used until confirmed |
|---|---|
| Reminder threshold (PR6) | 48 hours |
| Who decides on quotations | Any one designated approver |
| Who approves designs | All designated approvers of the project (one or more client users) |
| Manager assignment for new requests | First active project manager; editable |
| Project number format | `FS-YYYY-NNNN` |
| Project types | Store interior, display stand, brand sign, event booth, other |
| Stages after approval | Production → Delivery and Installation → Turnover |
| Down payment before design | Not tracked (payments are out of scope) |
| Upload limit and file types | 20 MB; JPG, PNG, WebP, PDF |
| Email sender and SMTP provider | Development log only |
| Roles merged for a small staff (for example owner also manager) | Allowed: a user has one role; admins can do everything managers can |
| Use period length for the evaluation | Two weeks (thesis Chapter 3) |
