import { describe, expect, it } from "vitest";

import { classLabel, groupByCrop, KNOWN_CLASSES } from "@/lib/classes";
import { en } from "@/lib/i18n/dictionaries/en";

describe("groupByCrop", () => {
  it("groups classes under their crop, both levels sorted", () => {
    const groups = groupByCrop(
      ["Tomato___Late_blight", "Potato___Late_blight", "Tomato___Early_blight"],
      en,
      "en",
    );

    expect(groups.map((group) => group.crop)).toEqual(["Potato", "Tomato"]);
    expect(groups[1]?.options.map((option) => option.condition)).toEqual([
      "Early blight",
      "Late blight",
    ]);
    expect(groups[1]?.options[0]?.className).toBe("Tomato___Early_blight");
  });

  it("covers every known class exactly once", () => {
    const groups = groupByCrop([...KNOWN_CLASSES], en, "en");

    expect(groups.flatMap((group) => group.options)).toHaveLength(KNOWN_CLASSES.length);
  });
});

describe("classLabel", () => {
  it("uses the dictionary for known classes", () => {
    expect(classLabel("Corn_(maize)___Common_rust_", en)).toEqual({
      crop: "Maize (corn)",
      condition: "Common rust",
      healthy: false,
    });
  });

  it("flags healthy classes", () => {
    expect(classLabel("Tomato___healthy", en).healthy).toBe(true);
  });

  it("falls back to a cleaned-up raw name for unknown classes", () => {
    expect(classLabel("Banana___Black_sigatoka", en)).toEqual({
      crop: "Banana",
      condition: "Black sigatoka",
      healthy: false,
    });
    expect(classLabel("Banana___healthy", en)).toEqual({
      crop: "Banana",
      condition: "Healthy",
      healthy: true,
    });
  });

  it("has an English label for every known class", () => {
    expect(Object.keys(en.classes).sort()).toEqual([...KNOWN_CLASSES].sort());
  });
});
