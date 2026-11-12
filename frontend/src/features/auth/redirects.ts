import type { CurrentUser } from "@/lib/types";

/** After sign-in: the page the user came for, if it is in their own area; else their home. */
export function destinationAfterSignIn(user: CurrentUser, next: string | null): string {
  const home = user.home_path;
  if (next && (next === home || next.startsWith(`${home}/`) || next.startsWith(`${home}?`))) {
    return next;
  }
  return home;
}
