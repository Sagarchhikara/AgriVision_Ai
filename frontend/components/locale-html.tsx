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
export function LocaleHtml({ className, children }: { className: string; children: ReactNode }) {
  const { locale } = useParams<{ locale?: string }>();
  return (
    // data-scroll-behavior: the landing page scrolls smoothly (app/landing.css), and
    // this tells Next.js to jump, not glide, when it resets scroll on navigation.
    <html
      lang={isLocale(locale) ? locale : DEFAULT_LOCALE}
      className={className}
      data-scroll-behavior="smooth"
    >
      {children}
    </html>
  );
}
