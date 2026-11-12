/** Shapes of the FabriSee API responses (see backend/apps/projects/presenters.py). */

export type Role = "client" | "admin" | "project_manager" | "designer" | "production";

export type Stage = "request" | "design" | "production" | "delivery_installation" | "turnover";

export type ProjectStatus = "active" | "on_hold" | "cancelled" | "completed";

export type ProjectType =
  "store_interior" | "display_stand" | "brand_sign" | "event_booth" | "other";

export type QuotationStatus = "draft" | "sent" | "accepted" | "returned" | "superseded";

export type RevisionStatus = "pending_approval" | "changes_requested" | "approved" | "superseded";

export type ApprovalState = "approved" | "changes_requested" | "pending" | "no_decision";

export type DocumentType =
  "reference" | "quotation" | "render" | "spec_sheet" | "turnover" | "other";

/** What the signed-in user may do; mirrors the capability map of the backend. */
export interface Permissions {
  view_all_projects: boolean;
  submit_request: boolean;
  submit_request_on_behalf: boolean;
  edit_projects: boolean;
  view_clients: boolean;
  manage_clients: boolean;
  manage_users: boolean;
  manage_settings: boolean;
  view_quotations: boolean;
  manage_quotations: boolean;
  decide_quotations: boolean;
  view_revisions: boolean;
  upload_revisions: boolean;
  decide_revisions: boolean;
  decide_on_behalf: boolean;
  change_stage: boolean;
  reopen_design: boolean;
  request_change: boolean;
  override_stage: boolean;
  upload_documents: boolean;
  view_dashboard: boolean;
  view_approvals: boolean;
  view_activity_log: boolean;
  export_activity: boolean;
  view_email_outbox: boolean;
}

export type Permission = keyof Permissions;

export interface CurrentUser {
  id: number;
  email: string;
  full_name: string;
  short_name: string;
  initials: string;
  role: Role;
  role_label: string;
  job_title: string;
  phone: string;
  client: { id: number; company_name: string } | null;
  is_company_staff: boolean;
  home_path: "/app" | "/portal";
  privacy_acknowledged_at: string | null;
  permissions: Permissions;
}

export interface UserBrief {
  id: number;
  full_name: string;
  short_name: string;
  initials: string;
  role: Role;
  role_label: string;
  job_title: string;
}

export interface Contact extends UserBrief {
  email: string;
  phone: string;
}

export interface FileRef {
  url: string;
  name: string;
  content_type: string;
  size_bytes: number | null;
  is_image: boolean;
  is_pdf: boolean;
}

export interface NextStep {
  code: string;
  text: string;
  waiting_on: "staff" | "client" | "none";
  action_needed: boolean;
  since: string | null;
  item: { kind: "quotation" | "revision"; id: number | null; label: string } | null;
}

export type StageDates = Record<Stage, string | null>;

export interface RevisionSummary {
  id: number;
  label: string;
  locked_at: string | null;
  thumbnail_url: string | null;
}

export interface ProjectCardData {
  id: number;
  project_number: string;
  title: string;
  client: { id: number; company_name: string };
  project_type: ProjectType;
  project_type_label: string;
  stage: Stage;
  stage_label: string;
  status: ProjectStatus;
  status_label: string;
  target_date: string;
  is_overdue: boolean;
  days_until_target: number;
  manager: UserBrief | null;
  next_step: NextStep;
  stage_dates: StageDates;
  approved_revision: RevisionSummary | null;
  last_activity_at: string;
  created_at: string;
}

export interface Quotation {
  id: number;
  version_no: number;
  label: string;
  amount: string;
  status: QuotationStatus;
  status_label: string;
  is_latest: boolean;
  notes: string;
  prepared_by: UserBrief | null;
  created_at: string;
  sent_at: string | null;
  decided_by: UserBrief | null;
  decided_at: string | null;
  decision: "accepted" | "returned" | null;
  client_comment: string;
  decided_on_behalf: boolean;
  decision_channel: string;
  decision_channel_label: string;
  recorded_by: UserBrief | null;
  last_reminded_at: string | null;
  file: FileRef;
}

export interface ApprovalLine {
  approver: UserBrief;
  decision: "approved" | "changes_requested" | null;
  state: ApprovalState;
  comment: string;
  decided_at: string | null;
  decided_on_behalf: boolean;
  decision_channel: string;
  decision_channel_label: string;
  recorded_by: UserBrief | null;
}

export interface Revision {
  id: number;
  revision_no: number;
  label: string;
  status: RevisionStatus;
  status_label: string;
  is_locked: boolean;
  locked_at: string | null;
  notes: string;
  uploaded_by: UserBrief | null;
  uploaded_at: string;
  last_reminded_at: string | null;
  alt_text: string;
  render: FileRef;
  spec_sheet: FileRef | null;
  thumbnail_url: string | null;
  approvals: ApprovalLine[];
  approved_count: number;
  approver_count: number;
}

export interface ClientDetails {
  id: number;
  company_name: string;
  /** Staff only: these fields are absent in the client portal. */
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
}

export interface ProjectDetail extends Omit<
  ProjectCardData,
  "client" | "manager" | "approved_revision"
> {
  client: ClientDetails;
  location: string;
  dimensions: string;
  description: string;
  manager: Contact | null;
  designer: UserBrief | null;
  created_by: UserBrief | null;
  design_reopened: boolean;
  requires_requote: boolean;
  approvers: Contact[];
  current_quotation: Quotation | null;
  current_revision: Revision | null;
  approved_revision: Revision | null;
  counts: { quotations: number; revisions: number; documents: number };
  viewer: { is_designated_approver: boolean; can_view_quotations: boolean };
}

export interface ProjectDocument {
  id: number;
  doc_type: DocumentType;
  doc_type_label: string;
  original_name: string;
  visible_to_client: boolean;
  uploaded_by: UserBrief | null;
  created_at: string;
  file: FileRef;
  thumbnail_url: string | null;
}

export interface StageUpdate {
  id: number;
  from_stage: Stage | "";
  from_stage_label: string;
  to_stage: Stage;
  to_stage_label: string;
  text: string;
  remarks: string;
  source: "rule" | "manual" | "override";
  source_label: string;
  updated_by: UserBrief | null;
  created_at: string;
}

export interface ActivityEntry {
  id: number;
  action: string;
  action_label: string;
  actor: UserBrief | null;
  actor_name: string | null;
  text: string;
  created_at: string;
  project?: { id: number; project_number: string; title: string } | null;
}

export interface Timeline {
  stage_updates: StageUpdate[];
  activity: ActivityEntry[];
}

export interface PendingDecision {
  kind: "quotation" | "revision";
  id: number | null;
  label: string;
  project: { id: number; project_number: string; title: string; client_name: string };
  waiting_since: string;
  waiting_hours: number;
  is_overdue: boolean;
  pending_approvers: UserBrief[];
  approver_count: number;
  decided_count: number;
  last_reminded_at: string | null;
}

export interface StageColumn {
  stage: Stage;
  stage_label: string;
  count: number;
  projects: ProjectCardData[];
}

export interface Dashboard {
  generated_at: string;
  role: Role;
  reminder_hours: number;
  kpis: {
    active_projects: number;
    waiting_for_client: number;
    overdue_items: number;
    overdue_decisions: number;
    overdue_projects: number;
    due_next_7_days: number;
  };
  stage_counts: Record<Stage, number>;
  by_stage: StageColumn[];
  pending_decisions: PendingDecision[];
  overdue_projects: ProjectCardData[];
  due_soon: ProjectCardData[];
  focus: { key: string; title: string; empty_text: string; projects: ProjectCardData[] } | null;
  recent_activity: ActivityEntry[];
}

export interface PendingApprovals {
  count: number;
  overdue_count: number;
  results: PendingDecision[];
}

export interface AppNotification {
  id: number;
  event: string;
  event_label: string;
  title: string;
  message: string;
  link: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  project: { id: number; project_number: string; title: string } | null;
}

export interface ClientRecord {
  id: number;
  company_name: string;
  contact_person: string;
  email: string;
  phone: string;
  address: string;
  notes: string;
  is_active: boolean;
  project_count: number;
  active_project_count: number;
  created_at: string;
}

export interface PrivacyNotice {
  title: string;
  blocks: Array<
    { type: "heading" | "paragraph"; text: string } | { type: "list"; items: string[] }
  >;
}

export interface DemoAccounts {
  password: string;
  accounts: Array<{
    email: string;
    full_name: string;
    role: Role;
    role_label: string;
    company: string | null;
    note: string;
  }>;
}
