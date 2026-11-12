import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";

import { api, ApiError, setUnauthorizedHandler } from "@/lib/api";
import { queryKeys } from "@/lib/query";
import type { CurrentUser, Permission } from "@/lib/types";

type AuthStatus = "loading" | "signed-in" | "signed-out" | "unreachable";

interface AuthContextValue {
  status: AuthStatus;
  user: CurrentUser | null;
  /** The reason the server could not be reached (status "unreachable"). */
  error: ApiError | null;
  /**
   * True after the user chose "Sign out". The sign-in page then starts fresh, and does not
   * bring the next person to the page the previous one was on.
   */
  signedOutByUser: boolean;
  /** True when the user's role allows this (what the UI may show; the API decides). */
  can: (permission: Permission) => boolean;
  signIn: (email: string, password: string) => Promise<CurrentUser>;
  signOut: () => Promise<void>;
  acknowledgePrivacy: () => Promise<CurrentUser>;
  retry: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/** The signed-in user, or null when nobody is signed in. */
async function fetchCurrentUser(signal?: AbortSignal): Promise<CurrentUser | null> {
  const session = await api.get<{ user: CurrentUser | null }>("/auth/session/", { signal });
  return session.user;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [signedOutByUser, setSignedOutByUser] = useState(false);

  const me = useQuery({
    queryKey: queryKeys.me,
    queryFn: ({ signal }) => fetchCurrentUser(signal),
    staleTime: 5 * 60_000,
  });

  // A 401 on any request means the session ended: show the sign-in page.
  useEffect(() => {
    setUnauthorizedHandler(() => queryClient.setQueryData(queryKeys.me, null));
    return () => setUnauthorizedHandler(null);
  }, [queryClient]);

  const signInMutation = useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      api.post<CurrentUser>("/auth/login/", credentials),
    onSuccess: (user) => {
      // Nothing of a previous user may stay in memory.
      queryClient.clear();
      queryClient.setQueryData(queryKeys.me, user);
    },
  });

  const signOutMutation = useMutation({
    mutationFn: () => api.post<void>("/auth/logout/"),
    onSettled: () => {
      queryClient.clear();
      queryClient.setQueryData(queryKeys.me, null);
    },
  });

  const acknowledgeMutation = useMutation({
    mutationFn: () => api.post<CurrentUser>("/auth/privacy-ack/"),
    onSuccess: (user) => queryClient.setQueryData(queryKeys.me, user),
  });

  const user = me.data ?? null;
  const status: AuthStatus = me.isPending
    ? "loading"
    : me.isError
      ? "unreachable"
      : user
        ? "signed-in"
        : "signed-out";

  const { mutateAsync: signInAsync } = signInMutation;
  const { mutateAsync: signOutAsync } = signOutMutation;
  const { mutateAsync: acknowledgeAsync } = acknowledgeMutation;
  const { refetch } = me;
  const error = me.error instanceof ApiError ? me.error : null;

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      error,
      can: (permission) => Boolean(user?.permissions[permission]),
      signedOutByUser,
      signIn: async (email, password) => {
        const signedIn = await signInAsync({ email, password });
        setSignedOutByUser(false);
        return signedIn;
      },
      signOut: async () => {
        setSignedOutByUser(true);
        await signOutAsync().catch(() => undefined);
      },
      acknowledgePrivacy: () => acknowledgeAsync(),
      retry: () => void refetch(),
    }),
    [status, user, error, signedOutByUser, signInAsync, signOutAsync, acknowledgeAsync, refetch],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}

/** The signed-in user. Use only below a route guard, where a user always exists. */
export function useCurrentUser(): CurrentUser {
  const { user } = useAuth();
  if (!user) throw new Error("useCurrentUser needs a signed-in user");
  return user;
}

/** The path of a project page for the area of the user. */
export function projectPath(user: Pick<CurrentUser, "home_path">, projectId: number, tab?: string) {
  const base = `${user.home_path}/projects/${projectId}`;
  return tab ? `${base}/${tab}` : base;
}
