/** Small builders of API objects for tests. */
import type { ApprovalLine, PendingDecision, Permissions, UserBrief } from "@/lib/types";

export function person(overrides: Partial<UserBrief> = {}): UserBrief {
  return {
    id: 1,
    full_name: "Mark Bautista",
    short_name: "M. Bautista",
    initials: "MB",
    role: "client",
    role_label: "Client",
    job_title: "Retail Operations Head",
    ...overrides,
  };
}

export function approvalLine(overrides: Partial<ApprovalLine> = {}): ApprovalLine {
  return {
    approver: person(),
    decision: null,
    state: "pending",
    comment: "",
    decided_at: null,
    decided_on_behalf: false,
    decision_channel: "",
    decision_channel_label: "",
    recorded_by: null,
    ...overrides,
  };
}

export function pendingDecision(overrides: Partial<PendingDecision> = {}): PendingDecision {
  return {
    kind: "revision",
    id: 9,
    label: "Design R2",
    project: {
      id: 4,
      project_number: "FS-2026-0004",
      title: "Experience counter and brand wall",
      client_name: "Aurelia Audio Labs",
    },
    waiting_since: "2026-11-08T09:00:00+08:00",
    waiting_hours: 96,
    is_overdue: true,
    pending_approvers: [person()],
    approver_count: 2,
    decided_count: 1,
    last_reminded_at: null,
    ...overrides,
  };
}

const NO_PERMISSIONS: Permissions = {
  view_all_projects: false,
  submit_request: false,
  submit_request_on_behalf: false,
  edit_projects: false,
  view_clients: false,
  manage_clients: false,
  manage_users: false,
  manage_settings: false,
  view_quotations: false,
  manage_quotations: false,
  decide_quotations: false,
  view_revisions: false,
  upload_revisions: false,
  decide_revisions: false,
  decide_on_behalf: false,
  change_stage: false,
  reopen_design: false,
  request_change: false,
  override_stage: false,
  upload_documents: false,
  view_dashboard: false,
  view_approvals: false,
  view_activity_log: false,
  export_activity: false,
  view_email_outbox: false,
};

/** A permission set with only the named permissions granted. */
export function permissions(...granted: (keyof Permissions)[]): Permissions {
  const result = { ...NO_PERMISSIONS };
  for (const name of granted) result[name] = true;
  return result;
}

export function allPermissions(): Permissions {
  return permissions(...(Object.keys(NO_PERMISSIONS) as (keyof Permissions)[]));
}
