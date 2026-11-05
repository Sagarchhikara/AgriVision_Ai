"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useI18n } from "@/components/i18n-provider";
import { LOCALE_COOKIE, LOCALE_NAMES, LOCALES, localePath, type Locale } from "@/lib/i18n/config";
import { cn } from "cn";

const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;

function rememberLocale(locale: Locale) {
  document.cookie = `${LOCALE_COOKIE}=${locale}; path=/; max-age=${ONE_YEAR_SECONDS}; samesite=lax`;
}

/**
 * All languages visible at once, as links in their own scripts, rather than a
 * menu: someone who can't read the current language can still find their own.
 */
export function LanguageSwitcher() {
  const { locale, t } = useI18n();
  const pathname = usePathname();
  const path = pathname.replace(/^\/[^/]+/, "") || "/";

  return (
    <nav aria-label={t.app.languageLabel}>
      <ul className="flex items-center gap-0.5">
        {LOCALES.map((code) => (
          <li key={code}>
            <Link
              href={localePath(code, path)}
              replace
              scroll={false}
              lang={code}
              hrefLang={code}
              aria-current={code === locale ? "true" : undefined}
              onClick={() => rememberLocale(code)}
              className={cn(
                "flex min-h-11 items-center rounded-lg px-2 text-sm focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none",
                code === locale
                  ? "bg-secondary font-semibold text-secondary-foreground underline underline-offset-4"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {LOCALE_NAMES[code]}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
