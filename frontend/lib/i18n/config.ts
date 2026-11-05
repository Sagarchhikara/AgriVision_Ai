import type { Language } from "@/lib/api";
import { en, type Dictionary } from "@/lib/i18n/dictionaries/en";

/** UI locales are exactly the backend's report languages, so one code drives both. */
export type Locale = Language;

export const DEFAULT_LOCALE: Locale = "en";

// Only English exists so far; Hindi and Punjabi arrive with locale routing.
const DICTIONARIES: Partial<Record<Locale, Dictionary>> = { en };

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale] ?? en;
}
