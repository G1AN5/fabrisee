/**
 * The only place that talks to the FabriSee API.
 *
 * Same-origin requests with the Django session cookie; unsafe methods send the CSRF
 * token from the `csrftoken` cookie in the `X-CSRFToken` header. Every failure is an
 * `ApiError` carrying the API's `{detail, code, fields}` error format.
 */

export type FieldErrors = Record<string, string[]>;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: FieldErrors;

  constructor(status: number, detail: string, code: string, fields: FieldErrors = {}) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields;
  }

  /** The server could not be reached at all (offline, or the API is not running). */
  get isNetworkError() {
    return this.status === 0;
  }
}

export type QueryParams = Record<string, string | number | boolean | null | undefined>;

interface RequestOptions {
  params?: QueryParams;
  body?: unknown;
  signal?: AbortSignal;
}

const API_BASE = "/api";
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

let onUnauthorized: (() => void) | null = null;

/** Called when any request (other than the auth endpoints) answers 401. */
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

export function getCookie(name: string): string | null {
  const prefix = `${name}=`;
  for (const part of document.cookie.split(";")) {
    const cookie = part.trim();
    if (cookie.startsWith(prefix)) {
      return decodeURIComponent(cookie.slice(prefix.length));
    }
  }
  return null;
}

export function buildUrl(path: string, params?: QueryParams): string {
  const url = `${API_BASE}${path}`;
  if (!params) return url;
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `${url}?${query}` : url;
}

function fallbackMessage(status: number): { detail: string; code: string } {
  if (status === 401) return { detail: "Please sign in to continue.", code: "not_authenticated" };
  if (status === 403)
    return { detail: "You do not have permission to do this.", code: "permission_denied" };
  if (status === 404)
    return { detail: "We could not find what you were looking for.", code: "not_found" };
  if (status === 429)
    return { detail: "Too many attempts. Wait a minute and try again.", code: "throttled" };
  if (status >= 500)
    return {
      detail: "The server had a problem. Please try again in a moment.",
      code: "server_error",
    };
  return { detail: "The request could not be completed.", code: "error" };
}

async function parseError(response: Response): Promise<ApiError> {
  const fallback = fallbackMessage(response.status);
  try {
    const data: unknown = await response.json();
    if (data && typeof data === "object") {
      const payload = data as { detail?: unknown; code?: unknown; fields?: unknown };
      return new ApiError(
        response.status,
        typeof payload.detail === "string" ? payload.detail : fallback.detail,
        typeof payload.code === "string" ? payload.code : fallback.code,
        payload.fields && typeof payload.fields === "object" ? (payload.fields as FieldErrors) : {},
      );
    }
  } catch {
    // Not JSON (for example a proxy error page): use the fallback message.
  }
  return new ApiError(response.status, fallback.detail, fallback.code);
}

async function request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers({ Accept: "application/json" });
  let body: BodyInit | undefined;

  if (options.body instanceof FormData) {
    body = options.body;
  } else if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }
  if (!SAFE_METHODS.has(method)) {
    const token = getCookie("csrftoken");
    if (token) headers.set("X-CSRFToken", token);
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, options.params), {
      method,
      headers,
      body,
      credentials: "same-origin",
      signal: options.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(
      0,
      "Cannot reach the FabriSee server. Check your connection and try again.",
      "network_error",
    );
  }

  if (!response.ok) {
    const apiError = await parseError(response);
    if (apiError.status === 401 && !path.startsWith("/auth/")) onUnauthorized?.();
    throw apiError;
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string, options?: Omit<RequestOptions, "body">) =>
    request<T>("GET", path, options),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body">) =>
    request<T>("POST", path, { ...options, body }),
  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body">) =>
    request<T>("PUT", path, { ...options, body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body">) =>
    request<T>("PATCH", path, { ...options, body }),
  delete: <T>(path: string, options?: Omit<RequestOptions, "body">) =>
    request<T>("DELETE", path, options),
};

/** A page of results from a list endpoint. */
export interface Paginated<T> {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
