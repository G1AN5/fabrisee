# 0001 — SQLite and Django as the backend

Date: 2026-11-11 · Status: accepted

## Context

FabriSee is the system of a BS IT thesis for one company (Five Brothers Solutions Inc.) and
its clients. The group has no server budget and no local development setup; everybody tries
the app in GitHub Codespaces. The thesis architecture (Chapter 3, Figure 12) is a React front
end, a Django back end with a REST API, a relational database, file storage, a scheduled
reminder task, and an email service.

## Decision

- **Django 5.2 LTS with Django REST Framework** on Python 3.12. Business rules (PR1 to PR9)
  live in service functions; views and serializers stay thin.
- **SQLite through the Django ORM**, one file in `backend/data/` that is never committed,
  opened in WAL mode with `IMMEDIATE` transactions so the web process and the scheduler can
  write without "database is locked" errors.
- **No third-party database or backend-as-a-service.** `DATABASE_URL` (dj-database-url) can
  point to PostgreSQL later without code changes, so the code avoids SQLite-only SQL.
- **Session authentication with CSRF on one origin.** The Vite dev server proxies `/api` to
  Django; in production Django serves the built React app. No JWT and no CORS.
- **Uploads on local disk** under `backend/media/`, served only through permission-checked
  API views.

## Consequences

- Zero setup: `python manage.py migrate` creates the database, so `make setup` is enough in a
  codespace, in CI, and on a laptop.
- The load of one company and its clients is far below what SQLite handles. If the group
  later needs several app servers, switching to PostgreSQL is a configuration change.
- A deployment must keep `backend/data/` and `backend/media/` on a persistent disk and back
  them up (Milestone 10).
- Rules that need row locks (project numbers, "one pending revision per project") rely on
  transactions plus database constraints, which work on both SQLite and PostgreSQL.
