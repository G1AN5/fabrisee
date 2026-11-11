import {
  Bell,
  Building2,
  ClipboardCheck,
  FolderKanban,
  LayoutDashboard,
  type LucideIcon,
  Mail,
  Settings,
  Users,
} from "lucide-react";

import type { Permission, Permissions } from "@/lib/types";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  /** Match the address exactly (the dashboard at /app). */
  end?: boolean;
  /** Shown only to roles with this permission. */
  permission?: Permission;
  /** Listed under "Administration". */
  admin?: boolean;
}

/** The navigation of the staff workspace (build guide, section 10.2). */
export const STAFF_NAV: NavItem[] = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/app/projects", label: "Projects", icon: FolderKanban },
  { to: "/app/approvals", label: "Approvals", icon: ClipboardCheck, permission: "view_approvals" },
  { to: "/app/clients", label: "Clients", icon: Building2, permission: "view_clients" },
  { to: "/app/notifications", label: "Notifications", icon: Bell },
  { to: "/app/users", label: "Users", icon: Users, permission: "manage_users", admin: true },
  {
    to: "/app/settings",
    label: "Settings",
    icon: Settings,
    permission: "manage_settings",
    admin: true,
  },
  {
    to: "/app/email-outbox",
    label: "Email outbox",
    icon: Mail,
    permission: "view_email_outbox",
    admin: true,
  },
];

/** The items a user may see: staff see only the functions allowed for their role (PR9). */
export function visibleNavItems(permissions: Permissions): NavItem[] {
  return STAFF_NAV.filter((item) => !item.permission || permissions[item.permission]);
}
