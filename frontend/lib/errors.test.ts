import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api";
import { errorCodeOf, errorMessage } from "@/lib/errors";
import { en } from "@/lib/i18n/dictionaries/en";
import { PhotoError } from "@/lib/image";

describe("errorCodeOf", () => {
  it("reads codes from API and photo errors", () => {
    expect(errorCodeOf(new ApiError("image_too_large", "x", 413))).toBe("image_too_large");
    expect(errorCodeOf(new PhotoError("unreadable_image", "x"))).toBe("unreadable_image");
  });

  it("treats anything else, including codes newer than this build, as unknown", () => {
    expect(errorCodeOf(new Error("boom"))).toBe("unknown");
    const future = new ApiError("network_error", "x", null);
    Object.defineProperty(future, "code", { value: "some_new_code" });
    expect(errorCodeOf(future)).toBe("unknown");
  });
});

describe("errorMessage", () => {
  it("does not invite a retry when reports are switched off", () => {
    expect(errorMessage("report_disabled", en).body).not.toContain("again");
    expect(errorMessage("llm_timeout", en).body).toContain("again");
  });

  it("gives the same message for server- and client-detected oversize photos", () => {
    expect(errorMessage("image_too_large", en)).toBe(errorMessage("file_too_large", en));
  });
});
