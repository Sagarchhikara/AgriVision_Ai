"use client";

import { useParams } from "next/navigation";
import type { ReactNode } from "react";

import { DEFAULT_LOCALE, isLocale } from "@/lib/i18n/config";

/**
 * The <html> element, with `lang` taken from the URL.
 *
 * It lives in the root layout, above the [locale] segment, so that switching
 * language does not unmount AnalysisProvider and lose the user's photo. A
 * server root layout could not see the locale from up here, and a root layout
 * inside [locale] would be replaced whenever the locale changes.
 */
export function LocaleHtml({ children }: { children: ReactNode }) {
  const { locale } = useParams<{ locale?: string }>();
  return <html lang={isLocale(locale) ? locale : DEFAULT_LOCALE}>{children}</html>;
}
