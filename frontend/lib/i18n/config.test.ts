import { describe, expect, it } from "vitest";

import { isLocale, localePath, matchAcceptLanguage } from "@/lib/i18n/config";

describe("matchAcceptLanguage", () => {
  it("picks the highest-weighted supported language, ignoring regions", () => {
    expect(matchAcceptLanguage("hi-IN,hi;q=0.9,en;q=0.8")).toBe("hi");
    expect(matchAcceptLanguage("en;q=0.5,pa-IN;q=0.9")).toBe("pa");
  });

  it("skips unsupported languages", () => {
    expect(matchAcceptLanguage("ta-IN,hi;q=0.7")).toBe("hi");
  });

  it("falls back to the default", () => {
    expect(matchAcceptLanguage("ta-IN,fr;q=0.7")).toBe("en");
    expect(matchAcceptLanguage(null)).toBe("en");
    expect(matchAcceptLanguage("")).toBe("en");
  });
});

describe("localePath", () => {
  it("prefixes paths without a trailing slash at the root", () => {
    expect(localePath("hi", "/")).toBe("/hi");
    expect(localePath("pa", "/result")).toBe("/pa/result");
  });
});

describe("isLocale", () => {
  it("accepts only supported locales", () => {
    expect(isLocale("hi")).toBe(true);
    expect(isLocale("fr")).toBe(false);
    expect(isLocale(undefined)).toBe(false);
  });
});
