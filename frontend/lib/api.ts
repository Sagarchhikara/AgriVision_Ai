/**
 * Typed client for the AgriVision FastAPI backend.
 *
 * Every type here comes from lib/api-types.ts, which is generated from the
 * backend's OpenAPI schema (`npm run gen:api`), so a backend contract change
 * shows up as a type error rather than a runtime surprise.
 *
 * Every failure is thrown as an ApiError carrying a code: the backend's own
 * `error` value when it sent an ErrorResponse, or a client-side code when the
 * request never got a usable answer. A caller-initiated abort is rethrown
 * as-is (a DOMException named "AbortError"), since cancelling is not a failure.
 */

import type { components } from "@/lib/api-types";

type Schemas = components["schemas"];

export type ClassPrediction = Schemas["ClassPrediction"];
export type PredictResponse = Schemas["PredictWithReportResponse"];
export type Report = Schemas["ReportSchema"];
export type ReportRequest = Schemas["ReportRequest"];
export type ReportResponse = Schemas["ReportResponse"];
export type FeedbackRequest = Schemas["FeedbackRequest"];
export type FeedbackResponse = Schemas["FeedbackResponse"];
export type FeedbackVerdict = FeedbackRequest["verdict"];
export type HealthResponse = Schemas["HealthResponse"];
export type MetaResponse = Schemas["MetaResponse"];
export type Language = MetaResponse["languages"][number];

export type BackendErrorCode = Schemas["ErrorResponse"]["error"];

/** Failures with no ErrorResponse body: the request failed, or something other
 * than the backend (a proxy, a gateway) answered. */
export type ClientErrorCode =
  "network_error" | "timeout" | "service_unavailable" | "unexpected_response";

export type ApiErrorCode = BackendErrorCode | ClientErrorCode;

export class ApiError extends Error {
  readonly code: ApiErrorCode;
  /** HTTP status, or null when no response was received. */
  readonly status: number | null;

  constructor(code: ApiErrorCode, message: string, status: number | null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

export interface RequestOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
}

// Generous by design: users are often on slow mobile connections, and the
// timer covers downloading the response body (the Grad-CAM PNG) too.
const TIMEOUTS_MS = {
  status: 10_000,
  predict: 60_000,
  // The backend allows its LLM 30s and retries once on malformed output.
  report: 75_000,
  feedback: 20_000,
} as const;

const GATEWAY_STATUSES = new Set([502, 503, 504]);

function apiBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!url) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not set. Copy .env.example to .env.local.");
  }
  return url.replace(/\/+$/, "");
}

function isErrorResponse(body: unknown): body is Schemas["ErrorResponse"] {
  if (typeof body !== "object" || body === null) return false;
  const candidate = body as Record<string, unknown>;
  return (
    candidate.success === false &&
    typeof candidate.error === "string" &&
    typeof candidate.detail === "string"
  );
}

function errorFromResponse(status: number, body: unknown): ApiError {
  if (isErrorResponse(body)) {
    return new ApiError(body.error, body.detail, status);
  }
  // A reverse proxy's body-size limit answers before the backend can.
  if (status === 413) {
    return new ApiError("image_too_large", "Upload rejected as too large.", status);
  }
  if (GATEWAY_STATUSES.has(status)) {
    return new ApiError("service_unavailable", `Service unavailable (HTTP ${status}).`, status);
  }
  return new ApiError("unexpected_response", `Unexpected response (HTTP ${status}).`, status);
}

async function request<T>(
  path: string,
  init: RequestInit,
  defaultTimeoutMs: number,
  { signal, timeoutMs = defaultTimeoutMs }: RequestOptions,
): Promise<T> {
  signal?.throwIfAborted();
  // Outside the try: a missing base URL is a deployment bug, not a network failure.
  const url = `${apiBaseUrl()}${path}`;

  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const forwardAbort = () => controller.abort(signal?.reason);
  signal?.addEventListener("abort", forwardAbort, { once: true });

  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    const body: unknown = await response.json().catch((error: unknown) => {
      if (controller.signal.aborted) throw error;
      return undefined;
    });

    if (!response.ok) throw errorFromResponse(response.status, body);
    if (body === undefined) {
      throw new ApiError("unexpected_response", "Response was not valid JSON.", response.status);
    }
    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (timedOut) throw new ApiError("timeout", `No response within ${timeoutMs}ms.`, null);
    if (signal?.aborted) throw error;
    throw new ApiError("network_error", "Could not reach the server.", null);
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", forwardAbort);
  }
}

function postJson<T>(path: string, body: unknown, timeoutMs: number, options: RequestOptions) {
  return request<T>(
    path,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    timeoutMs,
    options,
  );
}

export function getHealth(options: RequestOptions = {}): Promise<HealthResponse> {
  return request("/health", { method: "GET" }, TIMEOUTS_MS.status, options);
}

export function getMeta(options: RequestOptions = {}): Promise<MetaResponse> {
  return request("/meta", { method: "GET" }, TIMEOUTS_MS.status, options);
}

/** Runs the classifier and Grad-CAM. Reports are requested separately via generateReport. */
export function predict(image: Blob, options: RequestOptions = {}): Promise<PredictResponse> {
  const form = new FormData();
  form.append("image", image, image instanceof File ? image.name : "leaf.jpg");
  return request("/predict", { method: "POST", body: form }, TIMEOUTS_MS.predict, options);
}

export function generateReport(
  body: ReportRequest,
  options: RequestOptions = {},
): Promise<ReportResponse> {
  return postJson("/report", body, TIMEOUTS_MS.report, options);
}

export function submitFeedback(
  body: FeedbackRequest,
  options: RequestOptions = {},
): Promise<FeedbackResponse> {
  return postJson("/feedback", body, TIMEOUTS_MS.feedback, options);
}
