import "server-only";

import type { Dictionary } from "@/lib/i18n/dictionaries/en";
import type { Locale } from "@/lib/i18n/config";

const LOADERS: Record<Locale, () => Promise<Dictionary>> = {
  en: () => import("@/lib/i18n/dictionaries/en").then((module) => module.en),
  hi: () => import("@/lib/i18n/dictionaries/hi").then((module) => module.hi),
  pa: () => import("@/lib/i18n/dictionaries/pa").then((module) => module.pa),
};

export function getDictionary(locale: Locale): Promise<Dictionary> {
  return LOADERS[locale]();
}
