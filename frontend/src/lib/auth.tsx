import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, type ReactNode, useContext, useEffect, useMemo } from "react";

import { api, ApiError, setUnauthorizedHandler } from "@/lib/api";
import { queryKeys } from "@/lib/query";
import type { CurrentUser, Permission } from "@/lib/types";

type AuthStatus = "loading" | "signed-in" | "signed-out" | "unreachable";

interface AuthContextValue {
  status: AuthStatus;
  user: CurrentUser | null;
  /** The reason the server could not be reached (status "unreachable"). */
  error: ApiError | null;
  /** True when the user's role allows this (what the UI may show; the API decides). */
  can: (permission: Permission) => boolean;
  signIn: (email: string, password: string) => Promise<CurrentUser>;
  signOut: () => Promise<void>;
  acknowledgePrivacy: () => Promise<CurrentUser>;
  retry: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/** The signed-in user, or null when nobody is signed in (the API answers 401). */
async function fetchCurrentUser(signal?: AbortSignal): Promise<CurrentUser | null> {
  try {
    return await api.get<CurrentUser>("/auth/me/", { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();

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
      signIn: (email, password) => signInAsync({ email, password }),
      signOut: async () => {
        await signOutAsync().catch(() => undefined);
      },
      acknowledgePrivacy: () => acknowledgeAsync(),
      retry: () => void refetch(),
    }),
    [status, user, error, signInAsync, signOutAsync, acknowledgeAsync, refetch],
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
