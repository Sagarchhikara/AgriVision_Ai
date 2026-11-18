import { describe, expect, it } from "vitest";

import { centerSquare, fitWithin, MODEL_CROP_FRACTION } from "@/lib/image";

describe("fitWithin", () => {
  it("scales the longest side down to the limit, keeping the aspect ratio", () => {
    expect(fitWithin({ width: 4000, height: 3000 }, 1024)).toEqual({ width: 1024, height: 768 });
    expect(fitWithin({ width: 3000, height: 4000 }, 1024)).toEqual({ width: 768, height: 1024 });
  });

  it("never scales up", () => {
    expect(fitWithin({ width: 640, height: 480 }, 1024)).toEqual({ width: 640, height: 480 });
  });
});

describe("centerSquare", () => {
  it("matches the backend's resize-to-255 then centre-crop-224", () => {
    expect(MODEL_CROP_FRACTION).toBeCloseTo(224 / 255);

    // Short side 765 -> scaled to 255 (x1/3) -> crop 224 -> 672px of the original.
    const rect = centerSquare({ width: 1020, height: 765 }, MODEL_CROP_FRACTION);
    expect(rect.size).toBeCloseTo(672);
    expect(rect.x).toBeCloseTo((1020 - 672) / 2);
    expect(rect.y).toBeCloseTo((765 - 672) / 2);
  });
});
