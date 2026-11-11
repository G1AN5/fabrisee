import type { CurrentUser } from "@/lib/types";

/** After sign-in: the page the user came for, if it is in their own area; else their home. */
export function destinationAfterSignIn(user: CurrentUser, next: string | null): string {
  if (next && next.startsWith(user.home_path) && !next.startsWith("//")) return next;
  return user.home_path;
}
