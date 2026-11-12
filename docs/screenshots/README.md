# Screenshots

Key screens of FabriSee with the demo data, captured by Playwright at the two sizes of the
definition of done: **1440 × 900** (`desktop-*.png`) and **390 × 844** (`mobile-*.png`), at
double pixel density.

Regenerate them when a screen changes, and commit the pictures that changed:

```bash
make reset-demo    # optional: a fresh copy of the demo data
make screenshots
```

The list of screens is in `frontend/e2e/screenshots.spec.ts`. The people, companies, and
projects in the pictures are the fictitious demo data of the build guide (Appendix B).

| File | Screen | Signed in as |
|---|---|---|
| `*-sign-in.png` | Sign-in page | nobody |
| `*-dashboard-manager.png` | Management dashboard | project manager |
| `desktop-dashboard-designer.png` | Dashboard, "Revisions to prepare" first | designer |
| `desktop-dashboard-production.png` | Dashboard, "Approved and ready to build" first | production staff |
| `*-projects-list.png` | Projects list (table on desktop, cards on a phone) | project manager |
| `*-project-overview.png` | Project page, Overview tab | project manager |
| `*-project-design-revisions.png` | Project page, Design revisions tab (R2 pending, R1 in the history) | project manager |
| `desktop-project-quotations.png` | Project page, Quotations tab (v1 returned, v2 draft) | project manager |
| `desktop-project-progress.png` | Project page, Progress tab (stage changes) | project manager |
| `desktop-project-documents.png` | Project page, Documents tab (project document repository) | project manager |
| `desktop-notifications.png` | Notifications | project manager |
| `*-portal-home.png` | Client portal, My projects with "Action needed" | client, designated approver |
| `*-portal-project.png` | Client portal, project page | client, designated approver |
| `*-portal-designs.png` | Client portal, Designs tab | client, designated approver |
| `*-portal-quotation.png` | Client portal, Quotation tab | client, designated approver |
