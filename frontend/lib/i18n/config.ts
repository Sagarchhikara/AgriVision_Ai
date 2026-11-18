/**
 * Locale constants and helpers. No dictionaries here: this module is imported
 * by client code and by the proxy, and strings should reach the browser one
 * language at a time, from the server (see lib/i18n/dictionaries.ts).
 */

import type { Language } from "@/lib/api";

/** UI locales are exactly the backend's report languages, so one code drives both. */
export type Locale = Language;

export const LOCALES: readonly Locale[] = ["en", "hi", "pa"];
export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_COOKIE = "NEXT_LOCALE";

/** The upload screen, where every "check a leaf" link leads. */
export const DIAGNOSE_PATH = "/diagnose";

/** Each language in its own script, so a reader can always find theirs. */
export const LOCALE_NAMES: Record<Locale, string> = {
  en: "English",
  hi: "हिन्दी",
  pa: "ਪੰਜਾਬੀ",
};

export function isLocale(value: string | undefined): value is Locale {
  return (LOCALES as readonly (string | undefined)[]).includes(value);
}

/** Prefixes an app path with the locale: ("hi", "/result") -> "/hi/result". */
export function localePath(locale: Locale, path: string): string {
  return path === "/" ? `/${locale}` : `/${locale}${path}`;
}

/** Picks the highest-weighted supported language from an Accept-Language header. */
export function matchAcceptLanguage(header: string | null): Locale {
  if (!header) return DEFAULT_LOCALE;
  const ranked = header
    .split(",")
    .map((entry) => {
      const [tag = "", ...parameters] = entry.trim().split(";");
      const weight = parameters.find((parameter) => parameter.trim().startsWith("q="));
      return {
        language: tag.trim().split("-")[0]?.toLowerCase(),
        quality: weight ? Number(weight.trim().slice(2)) : 1,
      };
    })
    .sort((a, b) => b.quality - a.quality);
  return (
    (ranked.find(({ language }) => isLocale(language))?.language as Locale | undefined) ??
    DEFAULT_LOCALE
  );
}
