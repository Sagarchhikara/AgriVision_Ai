"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n-provider";
import { LanguageSwitcher } from "@/components/language-switcher";
import { Wordmark } from "@/components/wordmark";

export function SiteHeader() {
  const { t, href } = useI18n();
  return (
    <header className="sticky top-0 z-20 border-b bg-card print:static">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-2 px-4 md:px-6 lg:px-8">
        <Link
          href={href("/")}
          aria-label={t.app.homeLink}
          className="-mx-1 flex min-h-11 items-center rounded-lg px-1"
        >
          <Wordmark name={t.app.name} />
        </Link>
        <LanguageSwitcher />
      </div>
    </header>
  );
}
