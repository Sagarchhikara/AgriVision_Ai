import { describe, expect, it } from "vitest";

import { en } from "@/lib/i18n/dictionaries/en";
import { hi } from "@/lib/i18n/dictionaries/hi";
import { pa } from "@/lib/i18n/dictionaries/pa";

/** Every string in a dictionary, keyed by its dotted path. */
function flatten(value: unknown, path = ""): [string, string][] {
  if (typeof value === "string") return [[path, value]];
  return Object.entries(value as object).flatMap(([key, child]) =>
    flatten(child, path ? `${path}.${key}` : key),
  );
}

// Writing systems: a string in these dictionaries must use its own script.
const SCRIPTS = { hi: /\p{Script=Devanagari}/u, pa: /\p{Script=Gurmukhi}/u };
const SAME_IN_EVERY_LANGUAGE = new Set(["app.name"]);

describe.each([
  ["hi", hi],
  ["pa", pa],
] as const)("%s dictionary", (locale, dictionary) => {
  const strings = flatten(dictionary);

  it("has exactly the English keys", () => {
    expect(strings.map(([path]) => path)).toEqual(flatten(en).map(([path]) => path));
  });

  it("is translated: no string is left in Latin script only", () => {
    const untranslated = strings
      .filter(([path]) => !SAME_IN_EVERY_LANGUAGE.has(path))
      .filter(([, value]) => !SCRIPTS[locale].test(value))
      .map(([path]) => path);

    expect(untranslated).toEqual([]);
  });

  it("keeps the app name visible in the home link's accessible name", () => {
    expect(dictionary.app.homeLink).toContain(dictionary.app.name);
  });
});
