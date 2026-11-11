import { ChevronsUpDown, LogOut, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";

import { Avatar } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { PrivacyNoticeDialog } from "@/features/auth/PrivacyNoticeDialog";
import { useAuth, useCurrentUser } from "@/lib/auth";
import { cn } from "@/lib/utils";

interface UserMenuProps {
  /**
   * `sidebar`: name and role on the dark staff sidebar.
   * `avatar`: only the initials (the client portal top bar).
   */
  variant?: "sidebar" | "avatar";
  className?: string;
}

/** Who is signed in, with the privacy notice and "Sign out". */
export function UserMenu({ variant = "avatar", className }: UserMenuProps) {
  const user = useCurrentUser();
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const [privacyOpen, setPrivacyOpen] = useState(false);
  const subtitle = user.client ? user.client.company_name : user.role_label;

  async function handleSignOut() {
    await signOut();
    navigate("/login", { replace: true });
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          className={cn(
            "flex items-center gap-3 rounded-md text-left transition-colors duration-150 ease-out",
            variant === "sidebar"
              ? "w-full p-2 text-sidebar-foreground hover:bg-sidebar-active"
              : "p-1 hover:bg-accent",
            className,
          )}
          aria-label={`Account menu of ${user.full_name}`}
        >
          <Avatar
            initials={user.initials}
            className={cn(
              variant === "sidebar" ? "bg-slate-700 text-white" : "size-9 bg-primary text-white",
            )}
          />
          {variant === "sidebar" && (
            <>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-white">
                  {user.full_name}
                </span>
                <span className="block truncate text-xs text-sidebar-muted">{subtitle}</span>
              </span>
              <ChevronsUpDown className="size-4 shrink-0 text-sidebar-muted" aria-hidden="true" />
            </>
          )}
        </DropdownMenuTrigger>
        <DropdownMenuContent align={variant === "sidebar" ? "start" : "end"} className="w-64">
          <DropdownMenuLabel className="flex flex-col gap-0.5">
            <span className="truncate">{user.full_name}</span>
            <span className="truncate text-xs font-normal text-muted-foreground">{user.email}</span>
            <span className="truncate text-xs font-normal text-muted-foreground">
              {user.client ? `${user.client.company_name} · ${user.role_label}` : user.role_label}
            </span>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={() => setPrivacyOpen(true)}>
            <ShieldCheck aria-hidden="true" />
            Privacy notice
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => void handleSignOut()}>
            <LogOut aria-hidden="true" />
            Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <PrivacyNoticeDialog open={privacyOpen} mode="read" onOpenChange={setPrivacyOpen} />
    </>
  );
}
