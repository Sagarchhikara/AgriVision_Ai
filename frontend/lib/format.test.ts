import { describe, expect, it } from "vitest";

import { formatPercent } from "@/lib/format";

describe("formatPercent", () => {
  it("rounds to whole percentages", () => {
    expect(formatPercent(0.9821, "en")).toBe("98%");
    expect(formatPercent(0, "en")).toBe("0%");
  });

  it("shows tiny non-zero values as <1% rather than 0%", () => {
    expect(formatPercent(0.004, "en")).toBe("<1%");
  });

  it("never claims certainty: values that would round to 100% show as >99%", () => {
    expect(formatPercent(0.9999, "en")).toBe(">99%");
    expect(formatPercent(1, "en")).toBe(">99%");
    expect(formatPercent(0.994, "en")).toBe("99%");
  });
});
