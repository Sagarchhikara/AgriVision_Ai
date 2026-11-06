import "server-only";

import type { Dictionary } from "@/lib/i18n/dictionaries/en";
import type { Locale } from "@/lib/i18n/config";
import type { LandingDictionary } from "@/lib/i18n/landing/en";

const LOADERS: Record<Locale, () => Promise<Dictionary>> = {
  en: () => import("@/lib/i18n/dictionaries/en").then((module) => module.en),
  hi: () => import("@/lib/i18n/dictionaries/hi").then((module) => module.hi),
  pa: () => import("@/lib/i18n/dictionaries/pa").then((module) => module.pa),
};

export function getDictionary(locale: Locale): Promise<Dictionary> {
  return LOADERS[locale]();
}

const LANDING_LOADERS: Record<Locale, () => Promise<LandingDictionary>> = {
  en: () => import("@/lib/i18n/landing/en").then((module) => module.landingEn),
  hi: () => import("@/lib/i18n/landing/hi").then((module) => module.landingHi),
  pa: () => import("@/lib/i18n/landing/pa").then((module) => module.landingPa),
};

export function getLandingDictionary(locale: Locale): Promise<LandingDictionary> {
  return LANDING_LOADERS[locale]();
}
