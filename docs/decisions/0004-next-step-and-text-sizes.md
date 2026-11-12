# 0004 — One source for "next step", and text sizes per area

Date: 2026-11-12 · Status: accepted

## Context

Two things appear on many screens and must not disagree with each other.

- What happens next on a project ("Please review design R2", "R2 waiting for 1 of 2 approvers"),
  which also drives "needs action", the pending decisions, and the numbers on the dashboard.
- The size of text and controls: the build guide asks for a 14 px base in the staff workspace
  and 16 px in the client portal, where clients decide on phones.

## Decisions

1. **The next step is computed in one place**, `backend/apps/projects/selectors.py`
   (`ProjectState`, `open_steps`, `next_step`, `pending_decisions`). The project list, the
   project page, the dashboard, the approvals page, and the client portal all read it. The
   sentence is written for the person who reads it (staff or client), and it says who has to
   act. The frontend shows the sentence; it does not work it out again.
2. **Text sizes are tokens that change per area.** `frontend/src/styles/globals.css` defines the
   type scale and the height of controls as CSS variables. The client portal sets
   `data-ui="portal"` on the page, which raises the base size to 16 px and the control height
   to 44 px. Components use the tokens (`text-sm`, `h-(--control-h)`) and need no portal
   variants of their own.

## Consequences

- A new process rule changes `open_steps` once, and every screen follows.
- The same component (for example `ProjectCard` or `ApprovalPanel`) is correct in both areas.
- Tests of the next-step sentences are in `backend/apps/projects/tests/test_selectors.py`.
