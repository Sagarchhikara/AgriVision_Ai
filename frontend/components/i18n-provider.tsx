"use client";

import { createContext, useContext, useMemo, type ReactNode } from "react";

import { localePath, type Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionaries/en";

interface I18nValue {
  locale: Locale;
  t: Dictionary;
  /** Locale-prefixed path for links and navigation. */
  href: (path: string) => string;
}

const I18nContext = createContext<I18nValue | null>(null);

/** `dictionary` comes from the server, so the browser only downloads the active language. */
export function I18nProvider({
  locale,
  dictionary,
  children,
}: {
  locale: Locale;
  dictionary: Dictionary;
  children: ReactNode;
}) {
  const value = useMemo(
    () => ({ locale, t: dictionary, href: (path: string) => localePath(locale, path) }),
    [locale, dictionary],
  );
  return <I18nContext value={value}>{children}</I18nContext>;
}

export function useI18n(): I18nValue {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used inside <I18nProvider>.");
  return value;
}
