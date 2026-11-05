import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, getHealth, predict } from "@/lib/api";

const BASE = "http://api.test";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

async function caught(promise: Promise<unknown>): Promise<unknown> {
  try {
    await promise;
  } catch (error) {
    return error;
  }
  throw new Error("expected the promise to reject");
}

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", `${BASE}/`);
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("api client", () => {
  it("returns the parsed body and strips the base URL's trailing slash", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { status: "healthy" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getHealth()).resolves.toEqual({ status: "healthy" });
    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/health`, expect.anything());
  });

  it("uploads the image as the multipart 'image' field", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, {}));
    vi.stubGlobal("fetch", fetchMock);

    await predict(new Blob(["x"], { type: "image/jpeg" }));
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect((init.body as FormData).get("image")).toBeInstanceOf(Blob);
  });

  it("surfaces the backend's error code from an ErrorResponse", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse(415, { success: false, error: "unsupported_image_type", detail: "nope" }),
        ),
    );

    const error = await caught(getHealth());
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ code: "unsupported_image_type", status: 415, message: "nope" });
  });

  it("maps a bare 413 from a proxy to image_too_large", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>", { status: 413 })));

    expect(await caught(getHealth())).toMatchObject({ code: "image_too_large", status: 413 });
  });

  it("maps a gateway error without an ErrorResponse to service_unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("Bad gateway", { status: 502 })));

    expect(await caught(getHealth())).toMatchObject({ code: "service_unavailable", status: 502 });
  });

  it("reports a failed fetch as network_error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    expect(await caught(getHealth())).toMatchObject({ code: "network_error", status: null });
  });

  it("reports a slow request as timeout", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal?.addEventListener("abort", () =>
              reject(new DOMException("aborted", "AbortError")),
            );
          }),
      ),
    );

    const pending = caught(getHealth({ timeoutMs: 1000 }));
    await vi.advanceTimersByTimeAsync(1000);
    expect(await pending).toMatchObject({ code: "timeout" });
  });

  it("rethrows a caller's abort untouched instead of reporting a failure", async () => {
    vi.stubGlobal("fetch", vi.fn());
    const controller = new AbortController();
    controller.abort();

    const error = await caught(getHealth({ signal: controller.signal }));
    expect(error).not.toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ name: "AbortError" });
  });

  it("fails loudly when the base URL is not configured", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "");
    vi.stubGlobal("fetch", vi.fn());

    const error = await caught(getHealth());
    expect(error).not.toBeInstanceOf(ApiError);
    expect(String(error)).toContain("NEXT_PUBLIC_API_BASE_URL");
  });
});
