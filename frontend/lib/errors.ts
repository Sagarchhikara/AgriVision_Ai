/**
 * Maps every failure the app can hit to a user-facing message.
 *
 * Keyed by code with a Record, so when `npm run gen:api` picks up a new
 * backend error code this file stops compiling until it is mapped.
 */

import { ApiError, type ApiErrorCode } from "@/lib/api";
import type { Dictionary } from "@/lib/i18n/dictionaries/en";
import { PhotoError, type PhotoErrorCode } from "@/lib/image";

export type AppErrorCode = ApiErrorCode | PhotoErrorCode | "unknown";

type MessageKey = Exclude<keyof Dictionary["errors"], "tryAgain">;

export interface ErrorMessage {
  title: string;
  body: string;
}

const MESSAGE_KEY: Record<AppErrorCode, MessageKey> = {
  // Backend
  invalid_image: "imageUnreadable",
  image_too_large: "imageTooLarge",
  unsupported_image_type: "imageType",
  invalid_feedback: "feedbackRejected",
  inference_error: "analysisFailed",
  report_error: "reportUnavailable",
  report_disabled: "reportUnavailable",
  llm_configuration_error: "reportUnavailable",
  llm_provider_error: "reportUnavailable",
  llm_timeout: "reportUnavailable",
  report_parse_error: "reportUnavailable",
  llm_rate_limited: "busy",
  validation_error: "unexpected",
  internal_error: "unexpected",
  // Client: no usable response
  network_error: "network",
  timeout: "timeout",
  service_unavailable: "serviceUnavailable",
  unexpected_response: "unexpected",
  // Client: photo preparation
  not_an_image: "imageType",
  file_too_large: "imageTooLarge",
  unreadable_image: "imageUnreadable",
  unknown: "unexpected",
};

function isAppErrorCode(code: string): code is AppErrorCode {
  return Object.hasOwn(MESSAGE_KEY, code);
}

/** The code for any thrown value; codes this build doesn't know become "unknown". */
export function errorCodeOf(error: unknown): AppErrorCode {
  if (error instanceof ApiError || error instanceof PhotoError) {
    return isAppErrorCode(error.code) ? error.code : "unknown";
  }
  return "unknown";
}

export function errorMessage(code: AppErrorCode, t: Dictionary): ErrorMessage {
  return t.errors[MESSAGE_KEY[code]];
}
