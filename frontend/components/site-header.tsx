"use client";

import { Sprout } from "lucide-react";
import Link from "next/link";

import { useI18n } from "@/components/i18n-provider";
import { LanguageSwitcher } from "@/components/language-switcher";

export function SiteHeader() {
  const { t, href } = useI18n();
  return (
    <header className="border-b border-border/70 bg-card/60">
      <div className="mx-auto flex h-14 max-w-xl items-center justify-between gap-2 px-4">
        <Link
          href={href("/")}
          aria-label={t.app.homeLink}
          className="-mx-2 flex min-h-11 items-center gap-2 rounded-lg px-2 text-lg font-semibold text-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          <Sprout aria-hidden className="size-6 shrink-0" />
          {/* The switcher needs the room on the narrowest phones. */}
          <span className="max-[345px]:sr-only">{t.app.name}</span>
        </Link>
        <LanguageSwitcher />
      </div>
    </header>
  );
}
