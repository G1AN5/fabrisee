# FabriSee progress

## Status

Current milestone: M0 (in progress) · Last updated: 2026-11-11

## Plan for this session (Session 1: M0 to M2)

1. **M0 Foundation** — repository layout, Django project, React app, design tokens, Makefile, dev
   container, CI, README, health endpoint.
2. **M1 Data model, authentication, roles, demo data** — all models of guide section 5, session
   sign-in, permission matrix, scoped querysets, `notify()` stub, `seed_demo` and `reset_demo`.
3. **M2 App shell, design system, read-only views** — sign-in page, privacy notice, staff workspace
   and client portal layouts, shared components, dashboard, project list, project pages,
   notification bell, 403 and 404 pages, first screenshots.

## Done

- (in progress) M0 Foundation

## Next

- M1 and M2 in this session, then Session 2 (M3 to M5).

## Decisions

- 2026-11-11 SQLite with WAL through the Django ORM; Django 5.2 LTS and DRF
  ([0001](docs/decisions/0001-sqlite-and-django.md)).
- 2026-11-11 TypeScript 6.0 (not 7), hand-written shadcn/ui primitives, no jsx-a11y lint plugin yet,
  Node 22 ([0002](docs/decisions/0002-frontend-toolchain-versions.md)).

## Implementation details to reflect in the thesis

- (filled in with M1)

## Questions for the group

- (filled in at the end of the session)

## Known issues

- (none yet)
