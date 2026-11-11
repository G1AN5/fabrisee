import { CircleCheck, Hammer, Inbox, type LucideIcon, PenTool, Truck } from "lucide-react";

import type { DocumentType, ProjectStatus, ProjectType, Stage } from "@/lib/types";

/** The five project stages, in order, with the look of their chip and tracker step. */
export interface StageInfo {
  value: Stage;
  label: string;
  /** A shorter label where space is tight (the tracker on phones). */
  shortLabel: string;
  icon: LucideIcon;
  /** Chip: text on tint with a border. */
  chip: string;
  /** Tracker step that is done or current. */
  solid: string;
  /** Text in the stage color. */
  text: string;
}

export const STAGES: StageInfo[] = [
  {
    value: "request",
    label: "Request",
    shortLabel: "Request",
    icon: Inbox,
    chip: "bg-stage-request-bg text-stage-request border-stage-request-border",
    solid: "bg-stage-request text-white border-stage-request",
    text: "text-stage-request",
  },
  {
    value: "design",
    label: "Design",
    shortLabel: "Design",
    icon: PenTool,
    chip: "bg-stage-design-bg text-stage-design border-stage-design-border",
    solid: "bg-stage-design text-white border-stage-design",
    text: "text-stage-design",
  },
  {
    value: "production",
    label: "Production",
    shortLabel: "Production",
    icon: Hammer,
    chip: "bg-stage-production-bg text-stage-production border-stage-production-border",
    solid: "bg-stage-production text-white border-stage-production",
    text: "text-stage-production",
  },
  {
    value: "delivery_installation",
    label: "Delivery and Installation",
    shortLabel: "Delivery",
    icon: Truck,
    chip: "bg-stage-delivery-bg text-stage-delivery border-stage-delivery-border",
    solid: "bg-stage-delivery text-white border-stage-delivery",
    text: "text-stage-delivery",
  },
  {
    value: "turnover",
    label: "Turnover",
    shortLabel: "Turnover",
    icon: CircleCheck,
    chip: "bg-stage-turnover-bg text-stage-turnover border-stage-turnover-border",
    solid: "bg-stage-turnover text-white border-stage-turnover",
    text: "text-stage-turnover",
  },
];

export const STAGE_ORDER: Stage[] = STAGES.map((stage) => stage.value);

export function stageInfo(stage: Stage): StageInfo {
  return STAGES.find((item) => item.value === stage) ?? STAGES[0]!;
}

export function stageIndex(stage: Stage): number {
  return STAGE_ORDER.indexOf(stage);
}

export type StepState = "done" | "current" | "upcoming";

/** Where a stage stands for a project: already done, the current one, or still to come. */

export function stepState(stage: Stage, current: Stage, status?: ProjectStatus): StepState {
  const position = stageIndex(stage);
  const currentPosition = stageIndex(current);
  if (position < currentPosition) return "done";
  if (position > currentPosition) return "upcoming";
  // A completed project has finished its last stage as well.
  return status === "completed" ? "done" : "current";
}

export const PROJECT_STATUS_LABELS: Record<ProjectStatus, string> = {
  active: "Active",
  on_hold: "On hold",
  cancelled: "Cancelled",
  completed: "Completed",
};

export const PROJECT_TYPE_LABELS: Record<ProjectType, string> = {
  store_interior: "Store interior",
  display_stand: "Display stand",
  brand_sign: "Brand sign",
  event_booth: "Event booth",
  other: "Other",
};

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  reference: "Reference files",
  quotation: "Quotations",
  render: "Renders",
  spec_sheet: "Spec sheets",
  turnover: "Turnover documents",
  other: "Other documents",
};

/** The order of the groups in the project document repository. */
export const DOCUMENT_TYPE_ORDER: DocumentType[] = [
  "turnover",
  "reference",
  "quotation",
  "render",
  "spec_sheet",
  "other",
];

/** Tabs of the project page in the staff workspace (the URL segment after the id). */
export const STAFF_PROJECT_TABS = [
  { value: "overview", label: "Overview" },
  { value: "quotations", label: "Quotations" },
  { value: "revisions", label: "Design revisions" },
  { value: "progress", label: "Progress" },
  { value: "documents", label: "Documents" },
  { value: "activity", label: "Activity" },
] as const;

/** Tabs of the project page in the client portal. */
export const PORTAL_PROJECT_TABS = [
  { value: "summary", label: "Summary" },
  { value: "quotation", label: "Quotation" },
  { value: "designs", label: "Designs" },
  { value: "progress", label: "Progress" },
  { value: "documents", label: "Documents" },
] as const;

export type StaffProjectTab = (typeof STAFF_PROJECT_TABS)[number]["value"];
export type PortalProjectTab = (typeof PORTAL_PROJECT_TABS)[number]["value"];

/** Upload rules (build guide, Appendix A; the server enforces its own setting). */
export const MAX_UPLOAD_MB = 20;
export const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
export const PDF_TYPE = "application/pdf";
