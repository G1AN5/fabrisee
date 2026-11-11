import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api, ApiError, buildUrl, getCookie, setUnauthorizedHandler } from "@/lib/api";

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("buildUrl", () => {
  it("prefixes /api and skips empty parameters", () => {
    expect(buildUrl("/projects/", { stage: "design", q: "", page: 2, client: undefined })).toBe(
      "/api/projects/?stage=design&page=2",
    );
    expect(buildUrl("/health/")).toBe("/api/health/");
  });
});

describe("api", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    document.cookie = "csrftoken=token-123";
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
    setUnauthorizedHandler(null);
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  });

  it("reads cookies by name", () => {
    expect(getCookie("csrftoken")).toBe("token-123");
    expect(getCookie("missing")).toBeNull();
  });

  it("sends the CSRF token and JSON body on unsafe requests", async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { ok: true }));

    await api.post("/auth/login/", { email: "pm@fabrisee.test" });

    const [url, init] = fetchMock.mock.calls[0]!;
    const headers = new Headers(init?.headers);
    expect(url).toBe("/api/auth/login/");
    expect(init?.method).toBe("POST");
    expect(init?.credentials).toBe("same-origin");
    expect(headers.get("X-CSRFToken")).toBe("token-123");
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(init?.body).toBe(JSON.stringify({ email: "pm@fabrisee.test" }));
  });

  it("does not send the CSRF token on GET requests", async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, []));

    await api.get("/projects/");

    const headers = new Headers(fetchMock.mock.calls[0]![1]?.headers);
    expect(headers.has("X-CSRFToken")).toBe(false);
  });

  it("turns API errors into ApiError with code and field messages", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(400, {
        detail: "Fill in the target date.",
        code: "PR1_MISSING_REQUIRED_FIELDS",
        fields: { target_date: ["Enter the target date."] },
      }),
    );

    const error = await api.post("/projects/requests/", {}).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 400,
      code: "PR1_MISSING_REQUIRED_FIELDS",
      message: "Fill in the target date.",
      fields: { target_date: ["Enter the target date."] },
    });
  });

  it("uses a plain message when the error is not JSON", async () => {
    fetchMock.mockResolvedValue(new Response("<html>Bad gateway</html>", { status: 502 }));

    const error = await api.get("/dashboard/").catch((e: unknown) => e);

    expect(error).toMatchObject({ status: 502, code: "server_error" });
  });

  it("reports an unreachable server as a network error", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

    const error = await api.get("/health/").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).isNetworkError).toBe(true);
  });

  it("calls the unauthorized handler on 401, except for the auth endpoints", async () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    fetchMock.mockImplementation(async () =>
      jsonResponse(401, { detail: "Sign in.", code: "not_authenticated", fields: {} }),
    );

    await api.get("/auth/me/").catch(() => undefined);
    expect(handler).not.toHaveBeenCalled();

    await api.get("/projects/").catch(() => undefined);
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it("returns undefined for 204 responses", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(api.post("/auth/logout/")).resolves.toBeUndefined();
  });
});
