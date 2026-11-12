# 0003 — Permissions and visibility (PR9)

Date: 2026-11-12 · Status: accepted

## Context

Process rule PR9: clients see only their own projects, and staff see only the functions allowed
for their role. The permission matrix is in the build guide (section 7). The rule has to hold on
every path: the API, the file downloads, and the pages.

## Decisions

1. **One capability map per role.** `ROLE_CAPABILITIES` in `backend/apps/accounts/permissions.py`
   lists what each of the five roles may do. The DRF permission classes read it
   (`require(Capability.X)`), and the session endpoint sends the same list to the React app as
   `permissions`. The pages use it only to decide what to show (`can("view_approvals")`); the
   API decides what is allowed.
2. **Scoped querysets.** Every view starts from a selector that is already limited to what the
   user may see: `scoped_projects(user)`, `scoped_documents(user)`, `scoped_quotations(user)`,
   `scoped_revisions(user)`. Client users get the projects of their own client, only documents
   marked visible to the client, and only quotations that were sent. Production staff get no
   quotations, and only design revisions that already have a decision.
3. **"Not found" instead of "no access" for another client's records.** A client user who asks for
   a project, document, or file of another client gets **404**, the same answer as for a record
   that does not exist. The API does not confirm that the record exists.
4. **Files only through the API.** `GET /api/files/{kind}/{id}/` checks the same scope before it
   sends a file. Nothing under `backend/media/` is served directly.
5. **Rules about a particular project live in the services** of that feature (for example "only a
   designated approver of this project decides"), not in the capability map.

## Consequences

- A new screen or endpoint asks one question: which capability, and which scoped selector.
- The permission matrix is tested once per role and action
  (`backend/apps/accounts/tests/test_permissions.py`), and thesis test case TC7 covers a client
  opening another client's project and its files.
- Changing what a role may do is a one-line change in the capability map, plus the guide.
